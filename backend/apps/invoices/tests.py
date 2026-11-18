from rest_framework.test import APIClient
from decimal import Decimal
import uuid
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from apps.core.models import Organization, Employee
from apps.accounts.models import User, UserOrganization
from apps.invoices.models import Invoice, InvoiceItem, SupplierProductAlias, IikoProductEmbedding
from apps.invoices.services.calculation_service import PackagingCalculationService
from apps.invoices.services.matching_service import InvoiceMatchingService, normalize_product_name
from apps.invoices.services.iiko_invoice_service import IikoIncomingInvoiceService
from apps.invoices.services.embedding_service import EmbeddingService
from apps.invoices.tasks import sync_and_vectorize_organization_task


class PackagingCalculationServiceTest(TestCase):
    def test_calculate_pack_to_base(self):
        # 10 коробок по 2.5 кг = 25 кг, сумма 50000 ₸ -> цена за кг 2000 ₸
        res = PackagingCalculationService.calculate_item_values(
            raw_amount=Decimal("10"),
            raw_price=Decimal("5000"),
            raw_sum=Decimal("50000"),
            packaging_coefficient=Decimal("2.5")
        )
        self.assertEqual(res["iiko_amount"], Decimal("25.000"))
        self.assertEqual(res["iiko_price"], Decimal("2000.00"))
        self.assertEqual(res["sum_diff"], Decimal("0.00"))

    def test_calculate_with_penny_rounding_diff(self):
        # 3 упаковки по 1.33 кг = 3.99 кг, сумма 1000 ₸
        res = PackagingCalculationService.calculate_item_values(
            raw_amount=Decimal("3"),
            raw_price=Decimal("333.33"),
            raw_sum=Decimal("1000.00"),
            packaging_coefficient=Decimal("1.33")
        )
        self.assertEqual(res["iiko_amount"], Decimal("3.990"))
        # 1000 / 3.99 = 250.6265 -> 250.63
        self.assertEqual(res["iiko_sum"], Decimal("1000.00"))
        self.assertIsNotNone(res["sum_diff"])


class MatchingServiceTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org", slug="test-org")
        self.supp_id = uuid.uuid4()
        self.alias = SupplierProductAlias.objects.create(
            organization=self.org,
            supplier_id=self.supp_id,
            supplier_name="ТОО Фуд Мастер",
            raw_product_name="Сыр Моцарелла 45%",
            normalized_raw_name="сыр моцарелла 45",
            iiko_product_id=uuid.uuid4(),
            iiko_product_name="Сыр Моцарелла пицца 45% (блок)",
            default_packaging_coefficient=Decimal("5.0"),
            usage_count=5
        )

    def test_normalize_product_name(self):
        raw = '  Сыр "Моцарелла" 45% (упак.)  '
        norm = normalize_product_name(raw)
        self.assertIn("сыр", norm)
        self.assertIn("моцарелла", norm)
        self.assertNotIn('"', norm)

    def test_match_by_alias(self):
        service = InvoiceMatchingService(self.org)
        match = service.match_item(
            raw_name="Сыр Моцарелла 45%",
            supplier_id=str(self.supp_id),
            raw_amount=2.0,
            raw_price=5000.0,
            raw_sum=10000.0
        )
        self.assertEqual(match["match_status"], InvoiceItem.MATCH_STATUS_GREEN)
        self.assertEqual(match["match_source"], "knowledge_base")
        self.assertEqual(match["product_name"], "Сыр Моцарелла пицца 45% (блок)")
        self.assertEqual(match["packaging_coefficient"], 5.0)

    @patch.object(InvoiceMatchingService, 'get_cached_products')
    def test_fuzzy_match_catalog(self, mock_get_products):
        mock_get_products.return_value = [
            {"id": str(uuid.uuid4()), "name": "Филе куриное охлажденное 1кг", "code": "001", "unit": "кг", "containers": []},
            {"id": str(uuid.uuid4()), "name": "Говядина вырезка 1кг", "code": "002", "unit": "кг", "containers": []},
        ]
        service = InvoiceMatchingService(self.org)
        match = service.match_item(
            raw_name="Филе куриное охл.",
            raw_amount=5.0,
            raw_price=1200.0,
            raw_sum=6000.0
        )
        self.assertIn(match["match_status"], [InvoiceItem.MATCH_STATUS_GREEN, InvoiceItem.MATCH_STATUS_YELLOW])
        self.assertEqual(match["product_name"], "Филе куриное охлажденное 1кг")

    def test_filtering_dishes_with_assemble_and_keeping_direct(self):
        service = InvoiceMatchingService(self.org)
        pid_goods = str(uuid.uuid4())
        pid_dish_assemble = str(uuid.uuid4())
        pid_dish_direct = str(uuid.uuid4())
        pid_service = str(uuid.uuid4())
        pid_modifier = str(uuid.uuid4())

        strategies = {
            pid_dish_assemble.lower(): "ASSEMBLE",
            pid_dish_direct.lower(): "DIRECT",
        }

        raw_items = [
            {"id": pid_goods, "name": "Мука пшеничная в/с", "type": "GOODS", "mainUnit": "кг"},
            {"id": pid_dish_assemble, "name": "Пицца Маргарита", "type": "DISH", "mainUnit": "порц"},
            {"id": pid_dish_direct, "name": "Багет сырно-чесночный", "type": "DISH", "mainUnit": "шт"},
            {"id": pid_service, "name": "Аренда зала", "type": "SERVICE", "mainUnit": "час"},
            {"id": pid_modifier, "name": "Экстра сыр", "type": "MODIFIER", "mainUnit": "порц"},
        ]

        with patch.object(service, '_fetch_assembly_charts_strategies', return_value=strategies):
            with patch('httpx.Client.get') as mock_get:
                class MockResponse:
                    status_code = 200
                    def json(self):
                        return raw_items
                mock_get.return_value = MockResponse()
                self.org.iiko_server_url = "https://iiko.example.com"
                with patch('apps.loyalty.services.IikoServerAuthService.get_access_token', return_value="fake_token"):
                    filtered = service._fetch_products_from_iiko()

        filtered_ids = [p['id'] for p in filtered]
        self.assertIn(pid_goods, filtered_ids)
        self.assertIn(pid_dish_direct, filtered_ids)
        self.assertNotIn(pid_dish_assemble, filtered_ids)
        self.assertNotIn(pid_service, filtered_ids)
        self.assertNotIn(pid_modifier, filtered_ids)


class VectorizationTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Vector Org",
            slug="vector-org",
            vision_llm_provider="gemini",
            vision_llm_api_key="test-key",
            is_invoices_enabled=True
        )

    def test_vector_matching_with_pgvector_model(self):
        prod_id = uuid.uuid4()
        # Создаем тестовый вектор единичной длины
        vec = [0.0] * 768
        vec[0] = 1.0  # единичный вектор по первой оси

        IikoProductEmbedding.objects.create(
            organization=self.org,
            iiko_product_id=prod_id,
            name="Молоко пастеризованное 3.2% 1л",
            code="MOL01",
            unit="л",
            product_type="GOODS",
            embedding=vec
        )

        service = InvoiceMatchingService(self.org)
        # При совпадении вектора запроса (тоже vec)
        with patch.object(InvoiceMatchingService, 'get_cached_products', return_value=[]):
            with patch.object(EmbeddingService, 'is_configured', return_value=True):
                with patch.object(EmbeddingService, 'get_embedding', return_value=vec):
                    match = service.match_item(
                        raw_name="мол. паст 3.2%",
                        clean_name="молоко пастеризованное",
                        raw_amount=10.0,
                        raw_price=450.0,
                        raw_sum=4500.0
                    )

        self.assertIn(match["match_status"], [InvoiceItem.MATCH_STATUS_GREEN, InvoiceItem.MATCH_STATUS_YELLOW])
        self.assertEqual(match["product_id"], str(prod_id))
        self.assertEqual(match["product_name"], "Молоко пастеризованное 3.2% 1л")
        self.assertIn("vector", match["match_source"])

    def test_sync_and_vectorize_task(self):
        mock_prods = [
            {"id": str(uuid.uuid4()), "name": "Сахар белый 1кг", "code": "SAH01", "unit": "кг", "type": "GOODS"},
            {"id": str(uuid.uuid4()), "name": "Соль поваренная 1кг", "code": "SOL01", "unit": "кг", "type": "GOODS"},
        ]

        dummy_vec = [0.01] * 768
        with patch.object(InvoiceMatchingService, '_fetch_products_from_iiko', return_value=mock_prods):
            with patch.object(EmbeddingService, 'is_configured', return_value=True):
                with patch.object(EmbeddingService, 'get_embeddings_batch', return_value=[dummy_vec, dummy_vec]):
                    sync_and_vectorize_organization_task(self.org.id)

        embeddings = IikoProductEmbedding.objects.filter(organization=self.org)
        self.assertEqual(embeddings.count(), 2)
        first = embeddings.first()
        self.assertIsNotNone(first.embedding)
        self.assertEqual(len(first.embedding), 768)



class IikoIncomingInvoiceServiceTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Resto",
            slug="test-resto",
            iiko_server_url="https://iiko.example.com",
            is_invoices_enabled=True
        )
        self.invoice = Invoice.objects.create(
            organization=self.org,
            invoice_number="АВ-1029",
            invoice_date=timezone.now().date(),
            iiko_store_id=uuid.uuid4(),
            iiko_supplier_id=uuid.uuid4(),
            total_sum=Decimal("15000.00")
        )
        self.item = InvoiceItem.objects.create(
            invoice=self.invoice,
            num=1,
            raw_name="Томаты свежие",
            raw_amount=Decimal("10.000"),
            raw_price=Decimal("1500.00"),
            raw_sum=Decimal("15000.00"),
            iiko_product_id=uuid.uuid4(),
            iiko_product_name="Помидоры тепличные",
            iiko_amount=Decimal("10.000"),
            iiko_price=Decimal("1500.00"),
            iiko_sum=Decimal("15000.00")
        )

    def test_xml_generation_status_new(self):
        service = IikoIncomingInvoiceService(self.org)
        xml_str = service.build_invoice_xml(self.invoice)
        
        # Verify XML structure
        self.assertIn("<document>", xml_str)
        self.assertIn("<status>NEW</status>", xml_str)  # Must be NEW (черновик)
        self.assertIn(f"<incomingDocumentNumber>{self.invoice.invoice_number}</incomingDocumentNumber>", xml_str)
        self.assertIn("<items>", xml_str)
        self.assertIn("<amount>10.000</amount>", xml_str)
        self.assertIn("<price>1500.00</price>", xml_str)
        self.assertIn("<defaultStore>", xml_str)

    def test_xml_generation_different_stores(self):
        store_item = uuid.uuid4()
        self.invoice.has_different_stores = True
        self.invoice.save()
        self.item.iiko_store_id = store_item
        self.item.save()

        service = IikoIncomingInvoiceService(self.org)
        xml_str = service.build_invoice_xml(self.invoice)

        # When has_different_stores is True, defaultStore should NOT be present in header
        self.assertNotIn("<defaultStore>", xml_str)
        # Store should be present inside item
        self.assertIn(f"<store>{str(store_item).upper()}</store>", xml_str)

    def test_update_item_skip_knowledge_base(self):
        client = APIClient()
        user = User.objects.create_user(username="testacc", email="testacc@test.com", password="password")
        UserOrganization.objects.create(user=user, organization=self.org, role=UserOrganization.ROLE_ACCOUNTANT)
        client.force_authenticate(user=user)

        new_prod_id = uuid.uuid4()
        url = f"/api/invoices/documents/{self.invoice.id}/items/{self.item.id}/?organization_id={self.org.id}"
        resp = client.patch(url, {
            "raw_name": "Исправленное название товара",
            "iiko_product_id": str(new_prod_id),
            "iiko_product_name": "Товар в iiko",
            "skip_knowledge_base": True,
            "is_imprecise_recognition": True
        }, format='json')

        self.assertEqual(resp.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.raw_name, "Исправленное название товара")
        self.assertTrue(self.item.skip_knowledge_base)
        self.assertTrue(self.item.is_imprecise_recognition)

        # Check knowledge base was NOT created
        alias_exists = SupplierProductAlias.objects.filter(
            organization=self.org,
            raw_product_name="Исправленное название товара"
        ).exists()
        self.assertFalse(alias_exists)


from rest_framework.test import APITestCase


class InvoiceApiTest(APITestCase):
    def setUp(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.org = Organization.objects.create(
            name="Test Org Invoices",
            slug="test-org-inv",
            is_invoices_enabled=True,
            default_store_id=uuid.uuid4(),
            default_store_name="Основной склад"
        )
        self.user = User.objects.create_user(username="accountant", email="acc@test.com", password="password123")
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            role=UserOrganization.ROLE_ACCOUNTANT
        )
        self.employee = Employee.objects.create(
            organization=self.org,
            first_name="Иван",
            last_name="Шеф",
            telegram_id=999888,
            role="chef",
            can_upload_invoices=True
        )

    @patch('apps.invoices.views.process_invoice_ocr_task.delay')
    def test_upload_invoice_from_web_admin(self, mock_ocr_task):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_authenticate(user=self.user)
        
        file1 = SimpleUploadedFile("page1.jpg", b"fake image content 1", content_type="image/jpeg")
        file2 = SimpleUploadedFile("page2.jpg", b"fake image content 2", content_type="image/jpeg")
        
        response = self.client.post(
            "/api/invoices/upload/",
            {
                "organization_id": str(self.org.id),
                "source": "web_admin",
                "files": [file1, file2]
            },
            format="multipart"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["source"], "web_admin")
        self.assertEqual(len(response.data["images"]), 2)
        mock_ocr_task.assert_called_once()

    def test_upload_invoice_disabled_module(self):
        self.org.is_invoices_enabled = False
        self.org.save()
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            "/api/invoices/upload/",
            {"organization_id": str(self.org.id), "source": "web_admin"},
            format="multipart"
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_invoice(self):
        invoice = Invoice.objects.create(
            organization=self.org,
            internal_number="INV-DEL-001",
            status=Invoice.STATUS_PENDING
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/invoices/documents/{invoice.id}/?organization_id={self.org.id}")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Invoice.objects.filter(id=invoice.id).exists())

    def test_filter_invoices_by_supplier_and_number_and_date(self):
        import datetime
        inv1 = Invoice.objects.create(
            organization=self.org,
            internal_number="INV-FILTER-001",
            invoice_number="НАКЛ-101",
            invoice_date=datetime.date(2026, 11, 1),
            raw_supplier_name="ТОО Мясной Двор",
            total_sum=Decimal("25000.00")
        )
        inv2 = Invoice.objects.create(
            organization=self.org,
            internal_number="INV-FILTER-002",
            invoice_number="НАКЛ-202",
            invoice_date=datetime.date(2026, 11, 10),
            raw_supplier_name="ИП Молоко",
            total_sum=Decimal("15000.00")
        )

        self.client.force_authenticate(user=self.user)

        # 1. Фильтр по поставщику
        res = self.client.get(f"/api/invoices/documents/?organization_id={self.org.id}&supplier=Мясной")
        self.assertEqual(res.status_code, 200)
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        ids = [i['id'] for i in results]
        self.assertIn(inv1.id, ids)
        self.assertNotIn(inv2.id, ids)

        # 2. Фильтр по номеру
        res = self.client.get(f"/api/invoices/documents/?organization_id={self.org.id}&number=202")
        self.assertEqual(res.status_code, 200)
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        ids = [i['id'] for i in results]
        self.assertIn(inv2.id, ids)
        self.assertNotIn(inv1.id, ids)

        # 3. Фильтр по дате
        res = self.client.get(f"/api/invoices/documents/?organization_id={self.org.id}&date_from=2026-11-05&date_to=2026-11-15")
        self.assertEqual(res.status_code, 200)
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        ids = [i['id'] for i in results]
        self.assertIn(inv2.id, ids)
        self.assertNotIn(inv1.id, ids)

    def test_suppliers_list_includes_invoice_suppliers(self):
        Invoice.objects.create(
            organization=self.org,
            internal_number="INV-SUP-001",
            raw_supplier_name="ТОО Экзотик Фрут"
        )
        self.client.force_authenticate(user=self.user)
        # По умолчанию без include_raw не должно содержать неподтвержденных поставщиков
        res_default = self.client.get(f"/api/invoices/suppliers/?organization_id={self.org.id}")
        self.assertEqual(res_default.status_code, 200)
        names_default = [s['name'] for s in res_default.data]
        self.assertNotIn("ТОО Экзотик Фрут", names_default)

        # С флагом include_raw=true включает для фильтрации
        res = self.client.get(f"/api/invoices/suppliers/?organization_id={self.org.id}&include_raw=true")
        self.assertEqual(res.status_code, 200)
        names = [s['name'] for s in res.data]
        self.assertIn("ТОО Экзотик Фрут", names)



