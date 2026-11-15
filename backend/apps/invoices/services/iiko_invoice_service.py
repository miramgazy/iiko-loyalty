import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from django.utils import timezone
from django.db import models
import httpx

from apps.core.models import Organization
from apps.loyalty.services import IikoServerAuthService
from apps.invoices.models import Invoice, InvoiceItem, SupplierProductAlias
from apps.invoices.services.matching_service import normalize_product_name

logger = logging.getLogger(__name__)


class IikoIncomingInvoiceService:
    def __init__(self, organization: Organization):
        self.org = organization

    def build_invoice_xml(self, invoice: Invoice) -> str:
        """
        Формирует XML-структуру incomingInvoiceDto со статусом NEW.
        """
        doc_date = invoice.invoice_date or timezone.now().date()
        date_str = doc_date.strftime("%d.%m.%Y")

        doc_elem = ET.Element("document")

        doc_num_elem = ET.SubElement(doc_elem, "documentNumber")
        doc_num_elem.text = invoice.internal_number

        if invoice.invoice_number:
            inc_doc_num = ET.SubElement(doc_elem, "incomingDocumentNumber")
            inc_doc_num.text = invoice.invoice_number

        date_elem = ET.SubElement(doc_elem, "dateIncoming")
        date_elem.text = date_str

        status_elem = ET.SubElement(doc_elem, "status")
        status_elem.text = "NEW"  # Черновик / Непроведенная

        use_default_time = ET.SubElement(doc_elem, "useDefaultDocumentTime")
        use_default_time.text = "true"

        store_elem = ET.SubElement(doc_elem, "defaultStore")
        store_elem.text = str(invoice.iiko_store_id).upper() if invoice.iiko_store_id else ""

        supplier_elem = ET.SubElement(doc_elem, "supplier")
        supplier_elem.text = str(invoice.iiko_supplier_id).upper() if invoice.iiko_supplier_id else ""

        comment_elem = ET.SubElement(doc_elem, "comment")
        comment_elem.text = f"Импорт из AI-модуля накладных ({invoice.get_source_display()})"

        items_elem = ET.SubElement(doc_elem, "items")

        items = invoice.items.all().order_by('num', 'id')
        for idx, item in enumerate(items, start=1):
            item_elem = ET.SubElement(items_elem, "item")

            num_el = ET.SubElement(item_elem, "num")
            num_el.text = str(idx)

            prod_el = ET.SubElement(item_elem, "product")
            prod_el.text = str(item.iiko_product_id).upper() if item.iiko_product_id else ""

            amount_el = ET.SubElement(item_elem, "amount")
            amount_el.text = f"{float(item.iiko_amount):.3f}"

            act_amount_el = ET.SubElement(item_elem, "actualAmount")
            act_amount_el.text = f"{float(item.iiko_amount):.3f}"

            price_el = ET.SubElement(item_elem, "price")
            price_el.text = f"{float(item.iiko_price):.2f}"

            sum_el = ET.SubElement(item_elem, "sum")
            sum_el.text = f"{float(item.iiko_sum):.2f}"

            st_el = ET.SubElement(item_elem, "store")
            st_el.text = str(invoice.iiko_store_id).upper() if invoice.iiko_store_id else ""

            if item.iiko_container_id:
                cont_el = ET.SubElement(item_elem, "containerId")
                cont_el.text = str(item.iiko_container_id).upper()

        return ET.tostring(doc_elem, encoding='utf-8').decode('utf-8')

    def export_invoice_to_iiko(self, invoice: Invoice) -> dict:
        """
        Формирует XML incomingInvoiceDto и отправляет в iiko Server со статусом NEW (Черновик / Непроведенная).
        """
        if not self.org.iiko_server_url:
            raise ValueError("Не настроен адрес iiko Server (iiko_server_url) в настройках организации")

        if not invoice.iiko_store_id:
            raise ValueError("Для отправки в iiko необходимо выбрать склад оприходования")

        if not invoice.iiko_supplier_id:
            raise ValueError("Для отправки в iiko необходимо выбрать поставщика из справочника iiko")

        items = invoice.items.all().order_by('num', 'id')
        if not items.exists():
            raise ValueError("В накладной отсутствуют позиции для оприходования")

        # Проверка, что все строки имеют привязанный товар iiko
        unmatched_items = items.filter(iiko_product_id__isnull=True)
        if unmatched_items.exists():
            unmatched_names = ", ".join([f"#{it.num} '{it.raw_name}'" for it in unmatched_items[:3]])
            raise ValueError(f"Не все товары сопоставлены с номенклатурой iiko: {unmatched_names}...")

        auth = IikoServerAuthService(self.org)
        token = auth.get_access_token()
        base_url = self.org.iiko_server_url.rstrip('/')
        url = f"{base_url}/resto/api/documents/import/incomingInvoice"

        xml_str = self.build_invoice_xml(invoice)
        xml_payload = xml_str.encode('utf-8')
        headers = {"Content-Type": "application/xml; charset=utf-8"}

        try:
            with httpx.Client(timeout=45, verify=False) as client:
                resp = client.post(url, content=xml_payload, params={"key": token}, headers=headers)
                
                if resp.status_code != 200:
                    err_text = resp.text
                    logger.error(f"iiko Server rejected incoming invoice {invoice.id}: {resp.status_code} - {err_text}")
                    raise ValueError(f"iiko Server вернул ошибку ({resp.status_code}): {err_text}")

                # Разбор результата
                resp_xml = resp.text
                valid = "true"
                doc_number_result = invoice.internal_number
                
                try:
                    root = ET.fromstring(resp_xml)
                    valid = root.findtext("valid") or "true"
                    doc_number_result = root.findtext("documentNumber") or invoice.internal_number
                    warning = root.findtext("warning") or "false"
                    if valid == "false":
                        error_desc = root.findtext("error") or "Ошибка валидации документа в iiko"
                        raise ValueError(f"iiko не принял документ: {error_desc}")
                except ET.ParseError:
                    pass

                # Обновляем накладную
                invoice.status = Invoice.STATUS_SENT_TO_IIKO
                invoice.iiko_document_number = doc_number_result
                invoice.sent_to_iiko_at = timezone.now()
                invoice.error_message = ""
                invoice.save()

                # Непрерывное самообучение: сохраняем связки в SupplierProductAlias
                self._save_knowledge_base_aliases(invoice, items)

                return {
                    "success": True,
                    "document_number": doc_number_result,
                    "message": "Приходная накладная успешно создана в iiko Server со статусом 'Черновик / Непроведенная'"
                }
        finally:
            # Обязательно освобождаем слот лицензии
            try:
                auth.logout()
            except Exception:
                pass

    def _save_knowledge_base_aliases(self, invoice: Invoice, items):
        """
        Сохраняет или обновляет базу знаний (SupplierProductAlias) для самообучения.
        """
        for item in items:
            if not item.iiko_product_id or not item.raw_name:
                continue

            norm_name = normalize_product_name(item.raw_name)
            if not norm_name:
                continue

            alias, created = SupplierProductAlias.objects.get_or_create(
                organization=self.org,
                supplier_id=invoice.iiko_supplier_id,
                normalized_raw_name=norm_name,
                defaults={
                    'supplier_name': invoice.iiko_supplier_name or invoice.raw_supplier_name,
                    'raw_product_name': item.raw_name,
                    'iiko_product_id': item.iiko_product_id,
                    'iiko_product_name': item.iiko_product_name,
                    'default_packaging_coefficient': item.packaging_coefficient,
                    'default_container_id': item.iiko_container_id,
                    'default_container_name': item.iiko_container_name,
                    'usage_count': 1
                }
            )

            if not created:
                alias.supplier_name = invoice.iiko_supplier_name or invoice.raw_supplier_name
                alias.iiko_product_id = item.iiko_product_id
                alias.iiko_product_name = item.iiko_product_name
                alias.default_packaging_coefficient = item.packaging_coefficient
                alias.default_container_id = item.iiko_container_id
                alias.default_container_name = item.iiko_container_name
                alias.usage_count = models.F('usage_count') + 1
                alias.save(update_fields=[
                    'supplier_name', 'iiko_product_id', 'iiko_product_name',
                    'default_packaging_coefficient', 'default_container_id',
                    'default_container_name', 'usage_count', 'last_used_at'
                ])
