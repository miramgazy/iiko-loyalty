import logging
import xml.etree.ElementTree as ET
from decimal import Decimal
import httpx
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from apps.core.models import Organization, Employee
from apps.accounts.permissions import IsAccountantOrAdmin
from apps.loyalty.services import IikoServerAuthService
from apps.invoices.models import Invoice, InvoiceImage, InvoiceItem, SupplierProductAlias
from apps.invoices.serializers import (
    InvoiceListSerializer, InvoiceDetailSerializer, InvoiceItemSerializer,
    SupplierProductAliasSerializer
)
from apps.invoices.tasks import process_invoice_ocr_task
from apps.invoices.services.calculation_service import PackagingCalculationService
from apps.invoices.services.supplier_service import IikoSupplierService
from apps.invoices.services.matching_service import InvoiceMatchingService, normalize_product_name
from apps.invoices.services.iiko_invoice_service import IikoIncomingInvoiceService
from apps.invoices.services.vision_service import GeminiVisionAdapter, OpenAIVisionAdapter, AnthropicVisionAdapter

logger = logging.getLogger(__name__)


def get_current_organization(request) -> Organization:
    org_id = (
        request.data.get('organization_id') or
        request.query_params.get('organization_id') or
        request.headers.get('X-Organization-Id')
    )
    if org_id:
        return get_object_or_404(Organization, id=org_id)

    if hasattr(request.user, 'memberships'):
        mem = request.user.memberships.first()
        if mem:
            return mem.organization

    if hasattr(request.user, 'organization') and request.user.organization:
        return request.user.organization

    if getattr(request, 'customer', None) and request.customer.organization:
        return request.customer.organization

    telegram_id = getattr(request.user, 'telegram_id', None)
    if telegram_id:
        emp = Employee.objects.filter(telegram_id=telegram_id, is_active=True).first()
        if emp and emp.organization:
            return emp.organization

    return None


class InvoiceUploadView(APIView):
    """
    Загрузка сканов / фотографий / PDF накладной (из веб-админки или TMA).
    Создает документ со всеми страницами и передает в Celery.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        org = get_current_organization(request)
        if not org:
            return Response(
                {"error": "Организация не найдена. Пожалуйста, убедитесь, что вы авторизованы."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка включения модуля Invoices
        if not org.is_invoices_enabled:
            return Response(
                {"error": "Модуль распознавания накладных отключен для данной организации"},
                status=status.HTTP_403_FORBIDDEN
            )

        source = request.data.get('source', 'web_admin')
        raw_store_id = request.data.get('iiko_store_id') or getattr(org, 'default_store_id', None)
        store_id = None
        if raw_store_id:
            try:
                import uuid
                store_id = uuid.UUID(str(raw_store_id))
            except (ValueError, TypeError):
                store_id = None

        store_name = request.data.get('iiko_store_name') or getattr(org, 'default_store_name', '')

        # Проверка прав для TMA
        employee = None
        if source == 'tma':
            telegram_id = getattr(request.user, 'telegram_id', None)
            if telegram_id:
                employee = Employee.objects.filter(
                    organization=org,
                    telegram_id=telegram_id,
                    is_active=True,
                    can_upload_invoices=True
                ).first()
                if not employee and not getattr(request.user, 'is_superuser', False):
                    # Проверяем, может ли он быть управляющим
                    from apps.accounts.models import UserOrganization, User
                    is_mgr = UserOrganization.objects.filter(
                        user__telegram_id=telegram_id,
                        organization=org,
                        role__in=[UserOrganization.ROLE_ORG_MANAGER, UserOrganization.ROLE_SUPERUSER, UserOrganization.ROLE_SUPERADMIN]
                    ).exists() or User.objects.filter(telegram_id=telegram_id, is_superuser=True).exists()
                    if not is_mgr:
                        return Response(
                            {"error": "У вас нет прав на загрузку накладных в TMA. Обратитесь к управляющему."},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    tg_user = User.objects.filter(telegram_id=telegram_id).first()
                    first_name = tg_user.first_name if tg_user else getattr(request.user, 'first_name', 'Сотрудник')
                    last_name = tg_user.last_name if tg_user else getattr(request.user, 'last_name', '')
                    employee, _ = Employee.objects.get_or_create(
                        organization=org,
                        telegram_id=telegram_id,
                        defaults={
                            'first_name': first_name or 'Сотрудник',
                            'last_name': last_name or '',
                            'role': 'owner',
                            'can_upload_invoices': True,
                            'is_active': True,
                        }
                    )

        files = request.FILES.getlist('files') or request.FILES.getlist('file')
        if not files:
            return Response({"error": "Не передано ни одного файла накладной"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Создаем документ
            invoice = Invoice.objects.create(
                organization=org,
                source=source,
                uploaded_by=request.user if hasattr(request.user, 'is_staff') and request.user.is_staff else None,
                uploaded_by_employee=employee,
                iiko_store_id=store_id,
                iiko_store_name=store_name or "",
                status=Invoice.STATUS_PENDING
            )

            for idx, f in enumerate(files, start=1):
                is_pdf = f.name.lower().endswith('.pdf') or f.content_type == 'application/pdf'
                InvoiceImage.objects.create(
                    invoice=invoice,
                    image=f,
                    page_number=idx,
                    is_pdf=is_pdf
                )

            # Запуск фоновой Celery таски
            process_invoice_ocr_task.delay(invoice.id)

            serializer = InvoiceDetailSerializer(invoice, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception("Error creating invoice: %s", e)
            return Response(
                {"error": f"Ошибка сохранения накладной: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    CRUD и управление накладными: список, просмотр, редактирование, экспорт в iiko.
    """
    permission_classes = [permissions.IsAuthenticated, IsAccountantOrAdmin]
    serializer_class = InvoiceDetailSerializer

    def get_queryset(self):
        org = get_current_organization(self.request)
        if not org or not org.is_invoices_enabled:
            return Invoice.objects.none()

        qs = Invoice.objects.filter(organization=org).select_related('organization', 'uploaded_by', 'uploaded_by_employee')

        # Фильтрация по сотруднику (для TMA)
        only_my = self.request.query_params.get('only_my') == 'true'
        from apps.accounts.models import User, UserOrganization
        is_web_admin = False
        if isinstance(self.request.user, User):
            is_web_admin = self.request.user.is_superuser or UserOrganization.objects.filter(
                user=self.request.user,
                organization=org,
                role__in=[
                    UserOrganization.ROLE_ACCOUNTANT,
                    UserOrganization.ROLE_ORG_MANAGER,
                    UserOrganization.ROLE_ORG_ADMIN,
                    UserOrganization.ROLE_SUPERUSER,
                    UserOrganization.ROLE_SUPERADMIN,
                ]
            ).exists()

        if only_my or not is_web_admin:
            telegram_id = getattr(self.request.user, 'telegram_id', None)
            if telegram_id:
                qs = qs.filter(
                    Q(uploaded_by_employee__telegram_id=telegram_id) |
                    Q(uploaded_by__telegram_id=telegram_id)
                )
            else:
                qs = qs.none()

        # Фильтры
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Номер накладной
        number = self.request.query_params.get('number')
        if number:
            qs = qs.filter(
                Q(invoice_number__icontains=number) |
                Q(internal_number__icontains=number)
            )

        # Контрагент (поставщик)
        supplier_id = self.request.query_params.get('supplier_id')
        if supplier_id:
            try:
                import uuid
                sup_uuid = uuid.UUID(str(supplier_id))
                qs = qs.filter(iiko_supplier_id=sup_uuid)
            except (ValueError, TypeError):
                pass

        supplier = self.request.query_params.get('supplier')
        if supplier and not supplier_id:
            qs = qs.filter(
                Q(iiko_supplier_name__icontains=supplier) |
                Q(raw_supplier_name__icontains=supplier)
            )

        # Период дат
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(
                Q(invoice_date__gte=date_from) |
                Q(invoice_date__isnull=True, created_at__date__gte=date_from)
            )

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(
                Q(invoice_date__lte=date_to) |
                Q(invoice_date__isnull=True, created_at__date__lte=date_to)
            )

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(invoice_number__icontains=search) |
                Q(internal_number__icontains=search) |
                Q(raw_supplier_name__icontains=search) |
                Q(iiko_supplier_name__icontains=search)
            )

        return qs.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = InvoiceListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def perform_destroy(self, instance):
        for img in instance.images.all():
            if img.image:
                try:
                    img.image.delete(save=False)
                except Exception:
                    pass
        instance.delete()

    @action(detail=True, methods=['post'], url_path='reprocess')
    def reprocess(self, request, pk=None):
        """Повторный запуск OCR распознавания."""
        invoice = self.get_object()
        process_invoice_ocr_task.delay(invoice.id)
        return Response({"message": "Задача распознавания повторно поставлена в очередь"})

    @action(detail=True, methods=['patch'], url_path='update-header')
    def update_header(self, request, pk=None):
        """Обновление метаданных документа (склад, поставщик, номер, дата)."""
        invoice = self.get_object()
        data = request.data

        if 'iiko_store_id' in data:
            invoice.iiko_store_id = data['iiko_store_id']
            invoice.iiko_store_name = data.get('iiko_store_name', invoice.iiko_store_name)

        if 'iiko_supplier_id' in data:
            invoice.iiko_supplier_id = data['iiko_supplier_id']
            invoice.iiko_supplier_name = data.get('iiko_supplier_name', invoice.iiko_supplier_name)

        if 'invoice_number' in data:
            invoice.invoice_number = data['invoice_number']

        if 'invoice_date' in data:
            invoice.invoice_date = data['invoice_date']

        invoice.save()
        return Response(InvoiceDetailSerializer(invoice, context={'request': request}).data)

    @action(detail=True, methods=['patch'], url_path=r'items/(?P<item_id>\d+)')
    def update_item(self, request, pk=None, item_id=None):
        """
        Интерактивное обновление товарной позиции:
        привязка к iiko, изменение коэффициента фасовки, авторасчет копеек.
        """
        invoice = self.get_object()
        item = get_object_or_404(InvoiceItem, invoice=invoice, id=item_id)
        data = request.data

        if 'iiko_product_id' in data:
            item.iiko_product_id = data['iiko_product_id']
            item.iiko_product_name = data.get('iiko_product_name', item.iiko_product_name)
            item.iiko_product_code = data.get('iiko_product_code', item.iiko_product_code)
            item.match_status = InvoiceItem.MATCH_STATUS_GREEN
            item.match_source = 'manual'
            item.confidence = Decimal('1.00')

        if 'iiko_container_id' in data:
            item.iiko_container_id = data['iiko_container_id']
            item.iiko_container_name = data.get('iiko_container_name', '')

        packaging_coeff = Decimal(str(data.get('packaging_coefficient') or item.packaging_coefficient or 1.0))
        raw_amount = Decimal(str(data.get('raw_amount', item.raw_amount)))
        raw_price = Decimal(str(data.get('raw_price', item.raw_price)))
        raw_sum = Decimal(str(data.get('raw_sum', item.raw_sum)))

        # Пересчет
        calc = PackagingCalculationService.calculate_item_values(
            raw_amount=raw_amount,
            raw_price=raw_price,
            raw_sum=raw_sum,
            packaging_coefficient=packaging_coeff
        )

        item.packaging_coefficient = calc['packaging_coefficient']
        item.raw_amount = raw_amount
        item.raw_price = raw_price
        item.raw_sum = raw_sum
        item.iiko_amount = calc['iiko_amount']
        item.iiko_price = calc['iiko_price']
        item.iiko_sum = calc['iiko_sum']
        item.sum_diff = calc['sum_diff']
        item.save()

        return Response(InvoiceItemSerializer(item).data)

    @action(detail=True, methods=['post'], url_path='send-to-iiko')
    def send_to_iiko(self, request, pk=None):
        """Формирование и отправка приходной накладной в iiko Server со статусом NEW."""
        invoice = self.get_object()
        service = IikoIncomingInvoiceService(invoice.organization)
        try:
            res = service.export_invoice_to_iiko(invoice)
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class IikoStoresView(APIView):
    """Список складов iiko Server."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        org = get_current_organization(request)
        if not org or not org.iiko_server_url:
            return Response([])

        from django.core.cache import cache
        cache_key = f"iiko_stores_{org.id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        stores = []
        try:
            auth = IikoServerAuthService(org)
            token = auth.get_access_token()
            base_url = org.iiko_server_url.rstrip('/')
            url = f"{base_url}/resto/api/corporation/stores"

            with httpx.Client(timeout=20, verify=False) as client:
                resp = client.get(url, params={"key": token})
                if resp.status_code == 200:
                    try:
                        root = ET.fromstring(resp.text)
                        for elem in root.findall('.//corporateItemDto'):
                            sid = elem.findtext('id')
                            name = elem.findtext('name')
                            stype = elem.findtext('type')
                            if sid and name and stype == 'STORE':
                                stores.append({"id": sid, "name": name})
                    except ET.ParseError:
                        pass
        except Exception as e:
            logger.error(f"Error fetching stores for org {getattr(org, 'id', None)}: {e}")

        cache.set(cache_key, stores, timeout=1800)
        return Response(stores)


class IikoSuppliersView(APIView):
    """Список и создание поставщиков в iiko Server."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        org = get_current_organization(request)
        if not org:
            return Response([])

        service = IikoSupplierService(org)
        force = request.query_params.get('refresh') == 'true'
        suppliers = []
        try:
            suppliers = service.get_suppliers(force_refresh=force) or []
        except Exception as e:
            logger.warning("Could not fetch suppliers from iiko server: %s", e)
            suppliers = []

        # Объединяем с уникальными поставщиками из уже загруженных накладных организации
        existing_names = {s['name'].strip().lower() for s in suppliers if s.get('name')}
        invoice_suppliers = Invoice.objects.filter(organization=org).values_list('iiko_supplier_name', 'raw_supplier_name').distinct()
        for iiko_name, raw_name in invoice_suppliers:
            name = (iiko_name or raw_name or '').strip()
            if name and name.lower() not in existing_names:
                suppliers.append({
                    "id": None,
                    "name": name,
                    "code": "",
                    "inn": ""
                })
                existing_names.add(name.lower())

        suppliers.sort(key=lambda x: (x.get('name') or '').lower())
        return Response(suppliers)

    def post(self, request, *args, **kwargs):
        org = get_current_organization(request)
        name = request.data.get('name')
        if not name:
            return Response({"error": "Название поставщика обязательно"}, status=status.HTTP_400_BAD_REQUEST)

        inn = request.data.get('inn', '')
        code = request.data.get('code', '')
        phone = request.data.get('phone', '')

        service = IikoSupplierService(org)
        try:
            created = service.create_supplier(name=name, inn=inn, code=code, phone=phone)
            return Response(created, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class IikoProductsCatalogView(APIView):
    """Каталог товаров iiko для поиска и автодополнения в UI."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        org = get_current_organization(request)
        service = InvoiceMatchingService(org)
        catalog = service.get_cached_products()

        search = request.query_params.get('search', '').strip().lower()
        if search:
            catalog = [p for p in catalog if search in p['name'].lower() or search in (p.get('code') or '').lower()]

        return Response(catalog[:50])


class SupplierProductAliasViewSet(viewsets.ModelViewSet):
    """База знаний / самообучение (Связки поставщиков и номенклатуры)."""
    permission_classes = [permissions.IsAuthenticated, IsAccountantOrAdmin]
    serializer_class = SupplierProductAliasSerializer

    def get_queryset(self):
        org = get_current_organization(self.request)
        if not org or not org.is_invoices_enabled:
            return SupplierProductAlias.objects.none()
        qs = SupplierProductAlias.objects.filter(organization=org)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(raw_product_name__icontains=search) |
                Q(iiko_product_name__icontains=search) |
                Q(supplier_name__icontains=search)
            )
        return qs.order_by('-usage_count', '-last_used_at')

    def perform_create(self, serializer):
        org = get_current_organization(self.request)
        raw_name = serializer.validated_data.get('raw_product_name')
        norm_name = normalize_product_name(raw_name)
        serializer.save(organization=org, normalized_raw_name=norm_name)


class TestVisionConnectionView(APIView):
    """Тест подключения к Vision LLM."""
    permission_classes = [permissions.IsAuthenticated, IsAccountantOrAdmin]

    def post(self, request, *args, **kwargs):
        org = get_current_organization(request)
        if not org or not org.is_invoices_enabled:
            return Response({"success": False, "error": "Модуль накладных отключен для данной организации"}, status=status.HTTP_403_FORBIDDEN)

        provider = request.data.get('vision_llm_provider', 'gemini')
        model = request.data.get('vision_llm_model', 'gemini-2.5-flash')
        api_key = request.data.get('vision_llm_api_key')
        base_url = request.data.get('vision_llm_base_url')

        if not api_key or api_key == '••••••••':
            api_key = org.vision_llm_api_key

        if not api_key:
            return Response({"success": False, "error": "API-ключ не указан"}, status=status.HTTP_400_BAD_REQUEST)

        # Тестовый пинг к провайдеру
        import time
        start_time = time.time()

        try:
            if provider == 'gemini':
                test_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                if base_url:
                    test_url = f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": "Reply with 'OK'"}]}],
                    "generationConfig": {"maxOutputTokens": 5}
                }
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(test_url, json=payload)
                    resp.raise_for_status()

            elif provider in ('openai', 'deepseek'):
                test_url = (base_url or "https://api.openai.com/v1").rstrip('/') + "/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "Reply with OK"}],
                    "max_tokens": 5
                }
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(test_url, json=payload, headers=headers)
                    resp.raise_for_status()

            elif provider == 'anthropic':
                test_url = (base_url or "https://api.anthropic.com/v1").rstrip('/') + "/messages"
                headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "Reply with OK"}],
                    "max_tokens": 5
                }
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(test_url, json=payload, headers=headers)
                    resp.raise_for_status()

            latency_ms = int((time.time() - start_time) * 1000)
            return Response({
                "success": True,
                "message": f"Успешное подключение к {provider} ({model})",
                "latency_ms": latency_ms
            })
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Ошибка соединения: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
