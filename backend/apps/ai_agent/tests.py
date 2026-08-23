from django.test import TestCase
from apps.core.models import Organization
from apps.accounts.models import User
from apps.ai_agent.services import execute_tool

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

    def test_list_tables(self):
        res = execute_tool(self.org, "list_tables", {})
        self.assertIn("tables", res)
        self.assertTrue(len(res["tables"]) > 0)
        self.assertFalse(any("user" in t for t in res["tables"]))

    def test_get_table_schema(self):
        res = execute_tool(self.org, "get_table_schema", {"table_name": "core_organization"})
        self.assertIn("columns", res)
        self.assertEqual(res["table"], "core_organization")
        self.assertIn("name", res["columns"])

    def test_execute_sql_query_select(self):
        res = execute_tool(self.org, "execute_sql_query", {"query": "SELECT id, name FROM core_organization"})
        self.assertIn("results", res)
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["name"], "AI Org")

    def test_execute_sql_query_security(self):
        res = execute_tool(self.org, "execute_sql_query", {"query": "DELETE FROM core_organization"})
        self.assertIn("error", res)
        self.assertIn("Разрешены только SELECT", res["error"])

    def test_call_api_endpoint(self):
        res = execute_tool(
            self.org, 
            "call_api_endpoint", 
            {
                "method": "GET", 
                "path": f"/api/analytics/organizations/{self.org.id}/kpi/",
                "params": {"date": "2026-08-20"}
            },
            user=self.user
        )
        # User doesn't have permission for this org so it returns a 403 permission error dict
        self.assertIn("detail", res)
