from django.test import TestCase
from datetime import date
from apps.core.models import Organization
from apps.analytics.models import DailyOlapReport
from apps.analytics.services import get_dashboard_kpis, sync_daily_olap_for_date

class DashboardKpisTests(TestCase):
    def test_get_dashboard_kpis_empty(self):
        org = Organization.objects.create(
            name="Analytics Test Org",
            slug="analytics-test-org"
        )
        # Call with no reports in database
        kpis = get_dashboard_kpis(org, date(2026, 8, 19))
        self.assertEqual(kpis["revenue"]["value"], 0.0)
        self.assertEqual(kpis["profit"]["value"], 0.0)
        self.assertEqual(kpis["avg_check"]["value"], 0.0)
        self.assertEqual(kpis["checks_count"]["value"], 0)
        self.assertEqual(kpis["guests_count"]["value"], 0)
        self.assertEqual(kpis["foodcost_percent"]["value"], 0.0)

    def test_get_dashboard_kpis_with_data(self):
        org = Organization.objects.create(
            name="Analytics Test Org 2",
            slug="analytics-test-org-2"
        )
        DailyOlapReport.objects.create(
            organization=org,
            date=date(2026, 8, 19),
            revenue=1000.0,
            cost=400.0,
            checks_count=10,
            guests_count=15
        )
        DailyOlapReport.objects.create(
            organization=org,
            date=date(2026, 8, 12), # last week
            revenue=800.0,
            cost=300.0,
            checks_count=8,
            guests_count=12
        )
        kpis = get_dashboard_kpis(org, date(2026, 8, 19))
        self.assertEqual(kpis["revenue"]["value"], 1000.0)
        # last_week_diff_pct = ((1000 - 800) / 800) * 100 = 25%
        self.assertEqual(kpis["revenue"]["last_week_diff_pct"], 25.0)

from unittest.mock import patch, MagicMock

class OlapSyncTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Sync Test Org",
            slug="sync-test-org",
            iiko_api_base_url="https://api-ru.iiko.services/api/1",
            iiko_organization_id="12345678-1234-1234-1234-123456789012"
        )

    @patch("apps.loyalty.services.IikoAuthService.get_access_token")
    @patch("httpx.Client.post")
    def test_sync_daily_olap_flat_response_new_fields(self, mock_post, mock_get_token):
        mock_get_token.return_value = "mock_token"
        
        # Prepare mock response for flat dictionary format with new fields
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "DishSumInt": 1600.0,
                    "ProductCostBase.ProductCost": 400.0,
                    "DishDiscountSumInt": 50.0,
                    "UniqOrderId": 10,
                    "GuestNum": 15
                }
            ]
        }
        mock_post.return_value = mock_response

        # Execute sync
        target_date = date(2026, 8, 19)
        sync_daily_olap_for_date(self.org, target_date)

        # Check DB
        report = DailyOlapReport.objects.filter(organization=self.org, date=target_date).first()
        self.assertIsNotNone(report)
        self.assertEqual(float(report.revenue), 1600.0)
        self.assertEqual(float(report.cost), 400.0)
        self.assertEqual(float(report.discounts), 50.0)
        self.assertEqual(report.checks_count, 10)
        self.assertEqual(report.guests_count, 15)

    @patch("apps.loyalty.services.IikoAuthService.get_access_token")
    @patch("httpx.Client.post")
    def test_sync_daily_olap_nested_response_fallback_fields(self, mock_post, mock_get_token):
        mock_get_token.return_value = "mock_token"
        
        # Prepare mock response for columns-values nested format using fallback fields
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "columns": [
                {"name": "DishSumInt"},
                {"name": "DishCost.ProductCost"},
                {"name": "DishDiscountSumInt"},
                {"name": "ChecksCount"},
                {"name": "GuestNum"}
            ],
            "data": [
                {
                    "values": [1600.0, 400.0, 50.0, 10, 15]
                }
            ]
        }
        mock_post.return_value = mock_response

        # Execute sync
        target_date = date(2026, 8, 19)
        sync_daily_olap_for_date(self.org, target_date)

        # Check DB
        report = DailyOlapReport.objects.filter(organization=self.org, date=target_date).first()
        self.assertIsNotNone(report)
        self.assertEqual(float(report.revenue), 1600.0)
        self.assertEqual(float(report.cost), 400.0)
        self.assertEqual(float(report.discounts), 50.0)
        self.assertEqual(report.checks_count, 10)
        self.assertEqual(report.guests_count, 15)

from rest_framework.test import APIClient
from apps.accounts.models import User, UserOrganization
from rest_framework_simplejwt.tokens import RefreshToken

class OlapSyncViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst",
            email="analyst@example.com",
            password="password123"
        )
        self.org = Organization.objects.create(
            name="Sync View Org",
            slug="sync-view-org",
            is_analytics_enabled=True,
            iiko_api_base_url="https://api-ru.iiko.services/api/1"
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            role=UserOrganization.ROLE_ORG_MANAGER
        )
        
    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        refresh['user_type'] = 'employee'
        return str(refresh.access_token)

    @patch("apps.analytics.services.sync_daily_olap_for_date")
    @patch("apps.analytics.services.sync_hourly_olap_for_date")
    def test_sync_view_success(self, mock_sync_hourly, mock_sync_daily):
        mock_sync_daily.return_value = None
        mock_sync_hourly.return_value = None
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.user)}')
        response = self.client.post(
            f'/api/analytics/organizations/{self.org.id}/sync/',
            {"days": 3},
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(mock_sync_daily.call_count, 3)
        self.assertEqual(mock_sync_hourly.call_count, 3)

    @patch("apps.analytics.services.sync_daily_olap_for_date")
    @patch("apps.analytics.services.sync_hourly_olap_for_date")
    def test_sync_view_failure(self, mock_sync_hourly, mock_sync_daily):
        mock_sync_daily.side_effect = Exception("API connection timed out")
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.user)}')
        response = self.client.post(
            f'/api/analytics/organizations/{self.org.id}/sync/',
            {"days": 1},
            format='json'
        )
        
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.data["success"])
        self.assertIn("API connection timed out", response.data["error"])
