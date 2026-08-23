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
        expected_views = ["v_ai_daily_sales", "v_ai_payment_types", "v_ai_stop_list", "v_ai_product_purchases"]
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

