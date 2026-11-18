import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone

from apps.invoices.models import Invoice, InvoiceItem, IikoProductEmbedding
from apps.invoices.services.vision_service import VisionInvoiceService
from apps.invoices.services.matching_service import InvoiceMatchingService
from apps.invoices.services.supplier_service import IikoSupplierService
from apps.invoices.services.embedding_service import EmbeddingService
from apps.core.models import Organization

logger = logging.getLogger(__name__)


@shared_task(name='apps.invoices.tasks.process_invoice_ocr_task', bind=True, max_retries=2)
def process_invoice_ocr_task(self, invoice_id: int):
    logger.info(f"Starting Vision OCR and matching for invoice {invoice_id}")
    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        logger.error(f"Invoice {invoice_id} not found")
        return

    invoice.status = Invoice.STATUS_PROCESSING
    invoice.error_message = ""
    invoice.save(update_fields=['status', 'error_message', 'updated_at'])

    try:
        # 1. Vision LLM распознавание
        vision_service = VisionInvoiceService(invoice.organization)
        extracted_data = vision_service.process_invoice(invoice)

        # 2. Обновление метаданных документа
        invoice.raw_llm_response = extracted_data
        invoice.invoice_number = extracted_data.get('invoice_number') or invoice.invoice_number
        invoice.raw_supplier_name = extracted_data.get('supplier_name') or ""
        invoice.raw_supplier_inn = extracted_data.get('supplier_inn') or ""

        # Парсинг даты
        date_str = extracted_data.get('invoice_date')
        if date_str:
            try:
                invoice.invoice_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        if extracted_data.get('total_sum') is not None:
            try:
                invoice.total_sum = float(extracted_data['total_sum'])
            except Exception:
                pass

        if extracted_data.get('vat_sum') is not None:
            try:
                invoice.vat_sum = float(extracted_data['vat_sum'])
            except Exception:
                pass

        # 3. Авто-поиск поставщика в iiko
        supplier_service = IikoSupplierService(invoice.organization)
        matched_supplier = supplier_service.match_supplier_by_name_or_inn(
            invoice.raw_supplier_name, invoice.raw_supplier_inn
        )
        if matched_supplier and not invoice.iiko_supplier_id:
            invoice.iiko_supplier_id = matched_supplier['id']
            invoice.iiko_supplier_name = matched_supplier['name']

        # 4. Сопоставление строк товарных позиций
        matching_service = InvoiceMatchingService(invoice.organization)
        items_data = extracted_data.get('items', [])

        # Очищаем старые строки, если это повторный запуск
        invoice.items.all().delete()

        created_items = []
        for idx, it in enumerate(items_data, start=1):
            raw_name = it.get('raw_name', '').strip()
            clean_name = it.get('clean_name', '').strip()
            if not raw_name and not clean_name:
                continue

            raw_amount = float(it.get('raw_amount') or 0.0)
            raw_price = float(it.get('raw_price') or 0.0)
            raw_sum = float(it.get('raw_sum') or 0.0)
            raw_unit = str(it.get('raw_unit') or '')
            packaging_hint = str(it.get('packaging_hint') or '')

            match_res = matching_service.match_item(
                raw_name=raw_name,
                clean_name=clean_name,
                supplier_id=str(invoice.iiko_supplier_id) if invoice.iiko_supplier_id else None,
                raw_amount=raw_amount,
                raw_price=raw_price,
                raw_sum=raw_sum,
                packaging_hint=packaging_hint
            )

            created_items.append(
                InvoiceItem(
                    invoice=invoice,
                    num=idx,
                    raw_name=raw_name or clean_name,
                    clean_name=clean_name,
                    raw_unit=raw_unit,
                    raw_amount=raw_amount,
                    raw_price=raw_price,
                    raw_sum=raw_sum,
                    raw_vat_percent=it.get('raw_vat_percent'),
                    iiko_product_id=match_res['product_id'],
                    iiko_product_name=match_res['product_name'],
                    iiko_product_code=match_res['product_code'],
                    confidence=match_res['confidence'],
                    match_status=match_res['match_status'],
                    match_source=match_res['match_source'],
                    candidates=match_res.get('candidates', []),
                    packaging_coefficient=match_res['packaging_coefficient'],
                    iiko_container_id=match_res.get('container_id'),
                    iiko_container_name=match_res.get('container_name') or "",
                    iiko_product_unit=match_res.get('product_unit') or "",
                    iiko_amount=match_res['iiko_amount'],
                    iiko_price=match_res['iiko_price'],
                    iiko_sum=match_res['iiko_sum'],
                    sum_diff=match_res['sum_diff']
                )
            )

        InvoiceItem.objects.bulk_create(created_items)

        invoice.status = Invoice.STATUS_RECOGNIZED
        invoice.error_message = ""
        invoice.save()
        logger.info(f"Successfully recognized and matched invoice {invoice_id}: {len(created_items)} items created")

    except Exception as exc:
        logger.exception(f"Error during OCR processing of invoice {invoice_id}: {exc}")
        invoice.status = Invoice.STATUS_FAILED
        invoice.error_message = str(exc)
        invoice.save(update_fields=['status', 'error_message', 'updated_at'])


@shared_task(name='apps.invoices.tasks.sync_and_vectorize_all_organizations_task')
def sync_and_vectorize_all_organizations_task():
    """
    Ночная задача (01:00): синхронизирует и векторизует номенклатуру
    для всех активных организаций с включенным модулем накладных.
    """
    orgs = Organization.objects.filter(is_active=True, is_invoices_enabled=True)
    logger.info(f"Starting nightly sync & vectorization for {orgs.count()} organizations")
    for org in orgs:
        try:
            sync_and_vectorize_organization_task.delay(org.id)
        except Exception as e:
            logger.error(f"Error queueing vectorization for org {org.id}: {e}")


@shared_task(name='apps.invoices.tasks.sync_and_vectorize_organization_task', bind=True, max_retries=2)
def sync_and_vectorize_organization_task(self, org_id: int):
    """
    Синхронизирует отфильтрованную номенклатуру iiko (товары + позиции со списанием DIRECT)
    и генерирует векторные эмбеддинги для pgvector.
    """
    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        logger.error(f"Organization {org_id} not found for vectorization")
        return

    logger.info(f"Starting product sync and vectorization for organization {org.name} ({org_id})")

    matching_service = InvoiceMatchingService(org)
    raw_products = matching_service._fetch_products_from_iiko()
    if not raw_products:
        logger.warning(f"No products fetched from iiko for org {org_id}")
        return

    logger.info(f"Fetched {len(raw_products)} filtered products for org {org_id}")

    # 1. Синхронизируем записи номенклатуры в БД
    existing_embeddings = {
        str(e.iiko_product_id): e
        for e in IikoProductEmbedding.objects.filter(organization=org)
    }

    to_create = []
    to_update = []
    need_vectorization = []

    for p in raw_products:
        pid = str(p['id'])
        pname = p.get('name', '').strip()
        pcode = p.get('code') or ''
        punit = p.get('unit') or 'кг'
        ptype = p.get('type') or 'GOODS'
        containers = p.get('containers') or []

        if pid in existing_embeddings:
            obj = existing_embeddings[pid]
            changed = False
            if obj.name != pname:
                obj.name = pname
                obj.embedding = None  # Имя изменилось, нужен пересчет вектора
                changed = True
            if obj.code != pcode:
                obj.code = pcode
                changed = True
            if obj.unit != punit:
                obj.unit = punit
                changed = True
            if obj.product_type != ptype:
                obj.product_type = ptype
                changed = True
            if changed:
                to_update.append(obj)
            if obj.embedding is None:
                need_vectorization.append(obj)
        else:
            new_obj = IikoProductEmbedding(
                organization=org,
                iiko_product_id=pid,
                name=pname,
                code=pcode,
                unit=punit,
                product_type=ptype,
                containers=containers,
                embedding=None
            )
            to_create.append(new_obj)

    if to_create:
        IikoProductEmbedding.objects.bulk_create(to_create)
        # Добавляем созданные объекты в очередь на векторизацию
        need_vectorization.extend(to_create)

    if to_update:
        IikoProductEmbedding.objects.bulk_update(
            to_update, ['name', 'code', 'unit', 'product_type', 'embedding', 'updated_at']
        )

    logger.info(
        f"Products catalog synced for org {org_id}: created {len(to_create)}, updated {len(to_update)}, "
        f"need embeddings: {len(need_vectorization)}"
    )

    # 2. Вычисляем векторные эмбеддинги батчами
    emb_service = EmbeddingService(org)
    if not emb_service.is_configured():
        logger.warning(
            f"Embedding service not configured for org {org_id} (missing API key). "
            f"Catalog saved without vectors."
        )
        return

    if not need_vectorization:
        logger.info(f"All {len(raw_products)} products for org {org_id} already have embeddings.")
        return

    batch_size = 50
    total_embedded = 0
    for i in range(0, len(need_vectorization), batch_size):
        chunk = need_vectorization[i : i + batch_size]
        texts = [item.name for item in chunk]
        vectors = emb_service.get_embeddings_batch(texts, batch_size=batch_size)

        updated_chunk = []
        for item, vec in zip(chunk, vectors):
            if vec is not None:
                item.embedding = vec
                updated_chunk.append(item)

        if updated_chunk:
            IikoProductEmbedding.objects.bulk_update(updated_chunk, ['embedding', 'updated_at'])
            total_embedded += len(updated_chunk)

    logger.info(
        f"Successfully generated embeddings for {total_embedded}/{len(need_vectorization)} "
        f"products for org {org_id}"
    )

