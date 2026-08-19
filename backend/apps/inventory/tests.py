from django.test import TestCase
from django.utils import timezone
from datetime import date, datetime, timedelta
from unittest.mock import patch
from apps.core.models import Organization
from apps.inventory.models import (
    ProductPurchaseHistory, StopListHistory, ProductInventoryRule
)
from apps.analytics.models import HourlyOlapReport
from apps.inventory.services import (
    calculate_price_drift, calculate_lost_revenue_for_stop_list
)

class InventoryCalculationsTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Inventory Test Cafe",
            slug="inv-test-cafe",
            is_active=True,
            is_analytics_enabled=True
        )

    def test_price_drift_calculation(self):
        product_uuid = "12345678-1234-1234-1234-123456789012"
        
        # Create rule
        rule = ProductInventoryRule.objects.create(
            organization=self.org,
            product_id=product_uuid,
            product_name="Помидоры",
            min_stock=10.0,
            max_stock=50.0,
            target_price=500.0
        )
        
        # Create first purchase (older date)
        ProductPurchaseHistory.objects.create(
            organization=self.org,
            product_id=product_uuid,
            product_name="Помидоры",
            price=450.0,
            quantity=10.0,
            date=date.today() - timedelta(days=5)
        )
        
        # Create second purchase (newer date, price increased)
        ProductPurchaseHistory.objects.create(
            organization=self.org,
            product_id=product_uuid,
            product_name="Помидоры",
            price=540.0,
            quantity=15.0,
            date=date.today()
        )
        
        drift_data = calculate_price_drift(self.org)
        
        self.assertEqual(len(drift_data), 1)
        item = drift_data[0]
        self.assertEqual(item["product_name"], "Помидоры")
        self.assertEqual(item["price_old"], 450.0)
        self.assertEqual(item["price_new"], 540.0)
        self.assertEqual(item["diff_percent"], 20.0) # (540 - 450) / 450 = 20%
        self.assertEqual(item["cost_impact"], 1350.0) # (540 - 450) * 15 qty = 1350

    def test_stop_list_lost_revenue_calculation(self):
        product_uuid = "87654321-4321-4321-4321-210987654321"
        
        # Create stop-list record: Wednesday 12:00 to 14:00 (2 hours)
        start_dt = timezone.make_aware(datetime(2026, 8, 19, 12, 0, 0)) # Aug 19, 2026 is Wednesday
        end_dt = timezone.make_aware(datetime(2026, 8, 19, 14, 0, 0))
        
        record = StopListHistory.objects.create(
            organization=self.org,
            product_id=product_uuid,
            product_name="Пицца Пепперони",
            started_at=start_dt,
            ended_at=end_dt
        )
        
        # Add historical sales reports for Wednesday (week_day = 4 in postgres or week_day filter)
        # Hour 12: 2 pizzas sold for 1200 each
        HourlyOlapReport.objects.create(
            organization=self.org,
            product_id=product_uuid,
            product_name="Пицца Пепперони",
            date=date(2026, 8, 12), # Wednesday last week
            hour=12,
            quantity=2.0,
            revenue=2400.0
        )
        # Hour 13: 3 pizzas sold for 1200 each
        HourlyOlapReport.objects.create(
            organization=self.org,
            product_id=product_uuid,
            product_name="Пицца Пепперони",
            date=date(2026, 8, 12),
            hour=13,
            quantity=3.0,
            revenue=3600.0
        )
        
        calculate_lost_revenue_for_stop_list(record)
        
        # Total lost revenue: hour 12 (2400) + hour 13 (3600) = 6000
        # Total lost profit: 6000 * 0.65 = 3900
        self.assertAlmostEqual(float(record.lost_revenue), 6000.0, places=2)
        self.assertAlmostEqual(float(record.lost_profit), 3900.0, places=2)
