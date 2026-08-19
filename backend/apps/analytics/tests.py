from django.test import TestCase
from datetime import date
from apps.core.models import Organization
from apps.analytics.models import DailyOlapReport
from apps.analytics.services import get_dashboard_kpis

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
