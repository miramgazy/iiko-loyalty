from django.test import TestCase
from apps.core.models import Organization
from apps.accounts.models import User
from apps.analytics.models import DailyOlapReport
from apps.ai_agent.services import execute_tool, rewrite_and_validate_sql, parse_agent_response
import datetime

class AIAgentToolsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123"
        )
        self.org = Organization.objects.create(
            name="AI Org",
            slug="ai-org",
            is_analytics_enabled=True,
            is_ai_agent_enabled=True
        )
        # Populate daily sales data for SQL test
        self.report = DailyOlapReport.objects.create(
            organization=self.org,
            date=datetime.date(2026, 8, 20),
            revenue=150000.00,
            cost=50000.00,
            checks_count=100,
            guests_count=120
        )
        # Also create a report for a different organization to test multi-tenancy isolation
        self.other_org = Organization.objects.create(
            name="Other Org",
            slug="other-org",
            is_analytics_enabled=True,
            is_ai_agent_enabled=True
        )
        self.other_report = DailyOlapReport.objects.create(
            organization=self.other_org,
            date=datetime.date(2026, 8, 20),
            revenue=999999.00,
            cost=10000.00,
            checks_count=10,
            guests_count=15
        )

    def test_list_tables(self):
        res = execute_tool(self.org, "list_tables", {})
        self.assertIn("tables", res)
        # Should only list the whitelisted views
        expected_views = ["v_ai_daily_sales", "v_ai_payment_types", "v_ai_stop_list", "v_ai_product_purchases", "v_ai_food_cost"]
        self.assertEqual(sorted(res["tables"]), sorted(expected_views))


    def test_get_table_schema_valid(self):
        res = execute_tool(self.org, "get_table_schema", {"table_name": "v_ai_daily_sales"})
        self.assertIn("columns", res)
        self.assertEqual(res["table"], "v_ai_daily_sales")
        self.assertIn("revenue", res["columns"])

    def test_get_table_schema_invalid(self):
        res = execute_tool(self.org, "get_table_schema", {"table_name": "core_organization"})
        self.assertIn("error", res)
        self.assertIn("запрещен", res["error"])

    def test_sql_rewriter_isolation(self):
        # Verify SQL rewriting inserts tenant filter
        raw_sql = "SELECT revenue FROM v_ai_daily_sales"
        rewritten = rewrite_and_validate_sql(raw_sql, self.org.id)
        # It should wrap view access in a subquery containing the organization_id check
        self.assertIn("organization_id = 1", rewritten)
        self.assertIn("LIMIT 50", rewritten)

    def test_execute_sql_query_select_and_isolation(self):
        # Querying the view should return only this org's data
        res = execute_tool(self.org, "execute_sql_query", {"query": "SELECT revenue FROM v_ai_daily_sales"})
        self.assertIn("results", res)
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(float(res["results"][0]["revenue"]), 150000.00)

    def test_execute_sql_query_security_blacklist(self):
        res = execute_tool(self.org, "execute_sql_query", {"query": "DELETE FROM v_ai_daily_sales"})
        self.assertIn("error", res)
        self.assertIn("SELECT-запросы", res["error"])

    def test_execute_sql_query_security_tables(self):
        res = execute_tool(self.org, "execute_sql_query", {"query": "SELECT * FROM core_organization"})
        self.assertIn("error", res)
        self.assertIn("запрещен", res["error"])

    def test_execute_sql_query_security_multi_statement(self):
        res = execute_tool(self.org, "execute_sql_query", {"query": "SELECT * FROM v_ai_daily_sales; DROP TABLE v_ai_daily_sales;"})
        self.assertIn("error", res)
        self.assertIn("Допускается только один SQL-запрос", res["error"])

    def test_parse_agent_response_plain_text(self):
        text = "Просто аналитический ответ без графиков"
        res = parse_agent_response(text)
        self.assertEqual(res["response"], text)
        self.assertIsNone(res["chart"])

    def test_parse_agent_response_json(self):
        json_text = '{"text": "Анализ оплат", "chart": {"type": "pie", "title": "Оплаты", "data": [{"label": "Каспи", "value": 100}]}}'
        res = parse_agent_response(json_text)
        self.assertEqual(res["response"], "Анализ оплат")
        self.assertEqual(res["chart"]["type"], "pie")
        self.assertEqual(res["chart"]["title"], "Оплаты")

    def test_parse_agent_response_json_in_markdown(self):
        md_text = 'Вот данные:\n```json\n{"text": "Анализ продаж", "chart": {"type": "bar", "title": "Продажи", "data": []}}\n```\nНадеюсь это поможет.'
        res = parse_agent_response(md_text)
        self.assertEqual(res["response"], "Анализ продаж")
        self.assertEqual(res["chart"]["type"], "bar")


from unittest.mock import patch, MagicMock
from apps.analytics.models import FoodCostReport, ProductStockSnapshot
from apps.analytics.food_cost_service import (
    sync_theoretical_food_cost,
    take_stock_snapshot,
    calculate_actual_food_cost
)
from apps.inventory.models import ProductPurchaseHistory

class FoodCostTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="AI Org FC",
            slug="ai-org-fc",
            is_analytics_enabled=True,
            is_ai_agent_enabled=True
        )
        
    @patch('apps.analytics.services.IikoOlapService.get_olap_report')
    def test_sync_theoretical_food_cost(self, mock_get_olap):
        # Mock iiko OLAP response
        mock_get_olap.return_value = [
            {"DishCategory": "Kitchen", "DishSumInt": 1000.0, "ProductCostBase.ProductCost": 350.0},
            {"DishCategory": "Bar", "DishSumInt": 500.0, "ProductCostBase.ProductCost": 150.0}
        ]
        
        target_date = datetime.date(2026, 8, 20)
        sync_theoretical_food_cost(self.org, target_date)
        
        # Verify FoodCostReport created
        reports = FoodCostReport.objects.filter(organization=self.org, date=target_date)
        self.assertEqual(reports.count(), 3) # Kitchen, Bar, and "Все"
        
        kitchen_report = reports.get(category_name="Kitchen")
        self.assertEqual(float(kitchen_report.revenue), 1000.0)
        self.assertEqual(float(kitchen_report.theoretical_cost), 350.0)
        self.assertEqual(float(kitchen_report.theoretical_foodcost_percent), 35.0)
        
        all_report = reports.get(category_name="Все")
        self.assertEqual(float(all_report.revenue), 1500.0)
        self.assertEqual(float(all_report.theoretical_cost), 500.0)
        self.assertEqual(float(all_report.theoretical_foodcost_percent), 33.33) # round(500/1500 * 100, 2)

    @patch('apps.inventory.services.IikoInventoryService.fetch_stock_balances')
    def test_calculate_actual_food_cost(self, mock_fetch_balances):
        # 1. Mock first stock snapshot (Beginning)
        mock_fetch_balances.return_value = [
            {"productId": "00000000-0000-0000-0000-000000000001", "productName": "Meat", "balance": 10.0, "cost": 150.0},
            {"productId": "00000000-0000-0000-0000-000000000002", "productName": "Milk", "balance": 5.0, "cost": 20.0}
        ]
        start_date = datetime.date(2026, 8, 1)
        take_stock_snapshot(self.org, start_date)
        
        # 2. Mock second stock snapshot (Ending)
        mock_fetch_balances.return_value = [
            {"productId": "00000000-0000-0000-0000-000000000001", "productName": "Meat", "balance": 4.0, "cost": 150.0},
            {"productId": "00000000-0000-0000-0000-000000000002", "productName": "Milk", "balance": 2.0, "cost": 20.0}
        ]
        end_date = datetime.date(2026, 8, 15)
        take_stock_snapshot(self.org, end_date)
        
        # 3. Create purchases in between
        ProductPurchaseHistory.objects.create(
            organization=self.org,
            product_id="00000000-0000-0000-0000-000000000001",
            product_name="Meat",
            price=150.0,
            quantity=5.0,
            date=datetime.date(2026, 8, 5)
        )
        
        # Create Sales revenue for the period
        DailyOlapReport.objects.create(
            organization=self.org,
            date=datetime.date(2026, 8, 10),
            revenue=5000.0,
            cost=1200.0
        )
        
        # Theoretical report for overall restaurant
        FoodCostReport.objects.create(
            organization=self.org,
            date=end_date,
            category_name="Все",
            revenue=5000.0,
            theoretical_cost=1200.0,
            theoretical_foodcost_percent=24.0
        )
        
        # Calculate
        # Beginning value: 10 * 150 + 5 * 20 = 1500 + 100 = 1600
        # Ending value: 4 * 150 + 2 * 20 = 600 + 40 = 640
        # Purchases: 5 * 150 = 750
        # Actual COGS: 1600 + 750 - 640 = 1710
        # Actual FC%: 1710 / 5000 * 100 = 34.2%
        # Variance cost: 1710 - 1200 = 510
        # Variance %: 34.2% - 24.0% = 10.2%
        calculate_actual_food_cost(self.org, start_date, end_date)
        
        report = FoodCostReport.objects.get(organization=self.org, date=end_date, category_name="Все")
        self.assertEqual(float(report.actual_cost), 1710.0)
        self.assertEqual(float(report.actual_foodcost_percent), 34.2)
        self.assertEqual(float(report.variance_cost), 510.0)
        self.assertEqual(float(report.variance_percent), 10.2)

    def test_agent_view_allowed(self):
        # Create a report record
        FoodCostReport.objects.create(
            organization=self.org,
            date=datetime.date(2026, 8, 15),
            category_name="Все",
            revenue=1000.0,
            theoretical_cost=300.0,
            theoretical_foodcost_percent=30.0,
            actual_cost=350.0,
            actual_foodcost_percent=35.0,
            variance_percent=5.0
        )
        
        # Run tool query
        res = execute_tool(self.org, "execute_sql_query", {"query": "SELECT revenue, variance_percent FROM v_ai_food_cost"})
        self.assertIn("results", res)
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(float(res["results"][0]["revenue"]), 1000.0)
        self.assertEqual(float(res["results"][0]["variance_percent"]), 5.0)


