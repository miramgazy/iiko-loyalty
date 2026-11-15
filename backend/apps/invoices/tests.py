from decimal import Decimal
import uuid
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from apps.core.models import Organization, Employee
from apps.accounts.models import User, UserOrganization
from apps.invoices.models import Invoice, InvoiceItem, SupplierProductAlias
from apps.invoices.services.calculation_service import PackagingCalculationService
from apps.invoices.services.matching_service import InvoiceMatchingService, normalize_product_name
from apps.invoices.services.iiko_invoice_service import IikoIncomingInvoiceService


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


class IikoIncomingInvoiceServiceTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Resto",
            slug="test-resto",
            iiko_server_url="https://iiko.example.com"
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

