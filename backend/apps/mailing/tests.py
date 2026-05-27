from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import patch
from datetime import timedelta

from apps.core.models import Organization
from apps.accounts.models import UserOrganization
from apps.loyalty.models import Customer, Visit
from apps.mailing.models import MailingTask
from apps.mailing.tasks import check_scheduled_mailings, process_mailing_batch

User = get_user_model()

class MailingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(
            name="Test Cafe",
            slug="test-cafe",
            tg_bot_token="fake_token",
            tg_bot_username="test_cafe_bot"
        )
        self.admin = User.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
            password="password",
            first_name="Admin",
            telegram_id=11111,
            language="ru"
        )
        self.membership = UserOrganization.objects.create(
            user=self.admin,
            organization=self.org,
            role=UserOrganization.ROLE_ORG_MANAGER
        )
        self.client.force_authenticate(user=self.admin)

        # Create customers
        self.customer1 = Customer.objects.create(
            organization=self.org,
            telegram_id=22222,
            phone="+77071111111",
            first_name="Alice",
            is_bot_subscribed=True,
            language="ru"
        )
        self.customer2 = Customer.objects.create(
            organization=self.org,
            telegram_id=33333,
            phone="+77072222222",
            first_name="Bob",
            is_bot_subscribed=True,
            language="kz"
        )
        self.customer3 = Customer.objects.create(
            organization=self.org,
            telegram_id=44444,
            phone="+77073333333",
            first_name="Charlie",
            is_bot_subscribed=False,  # Subscribed=False
            language="ru"
        )

        # Create visits
        Visit.objects.create(customer=self.customer1, status='completed')

    def test_crud_mailings(self):
        # Create mailing task
        res = self.client.post('/api/mailings/', {
            "title": "Новогодняя акция",
            "message_ru": "Привет, {{user_name}}!",
            "message_kz": "Сәлем, {{user_name}}!",
            "scheduled_at": timezone.now() + timedelta(days=1),
            "audience_type": "all"
        }, format='json')
        self.assertEqual(res.status_code, 201)
        task_id = res.data["id"]

        # List mailing tasks
        res = self.client.get('/api/mailings/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

        # Update task
        res = self.client.patch(f'/api/mailings/{task_id}/', {
            "title": "Обновленная акция"
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["title"], "Обновленная акция")

        # Delete task
        res = self.client.delete(f'/api/mailings/{task_id}/')
        self.assertEqual(res.status_code, 204)

    def test_count_recipients(self):
        res = self.client.get('/api/mailings/count_recipients/', {
            "audience_type": "all",
            "organization_id": self.org.id
        })
        self.assertEqual(res.status_code, 200)
        # Only customer1 and customer2 are subscribed with telegram_id
        self.assertEqual(res.data["count"], 2)

        # Test active count (Alice has a visit, Bob does not)
        res = self.client.get('/api/mailings/count_recipients/', {
            "audience_type": "active",
            "organization_id": self.org.id
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)

        # Test inactive count
        res = self.client.get('/api/mailings/count_recipients/', {
            "audience_type": "inactive",
            "organization_id": self.org.id
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)

    @patch('apps.mailing.tasks.requests.post')
    def test_send_test(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True, "result": {"message_id": 999}}

        task = MailingTask.objects.create(
            organization=self.org,
            title="Тест",
            message_ru="Привет, {{user_name}}!",
            message_kz="Сәлем, {{user_name}}!",
            scheduled_at=timezone.now(),
            status="scheduled"
        )

        res = self.client.post(f'/api/mailings/{task.id}/send_test/', {
            "telegram_id": "11111"
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "success")

        # Verify telegram_id is updated in profile
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.telegram_id, 11111)

        # Check call parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("sendMessage", args[0])
        payload = kwargs["json"]
        self.assertEqual(payload["chat_id"], "11111")
        self.assertIn("[ТЕСТОВОЕ СООБЩЕНИЕ]", payload["text"])

    @patch('apps.mailing.tasks.requests.post')
    def test_send_test_preview(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True, "result": {"message_id": 999}}

        res = self.client.post('/api/mailings/send_test_preview/', {
            "telegram_id": "11111",
            "message_ru": "Привет, {{user_name}}!",
            "message_kz": "Сәлем, {{user_name}}!"
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "success")

        # Verify telegram_id is updated in profile
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.telegram_id, 11111)

        # Check call parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("sendMessage", args[0])
        payload = kwargs["json"]
        self.assertEqual(payload["chat_id"], "11111")
        self.assertIn("[ТЕСТОВОЕ СООБЩЕНИЕ]", payload["text"])

    @patch('apps.mailing.tasks.requests.post')
    def test_celery_mailing_task(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True, "result": {}}

        # Create scheduled task
        task = MailingTask.objects.create(
            organization=self.org,
            title="Рассылка на всех",
            message_ru="Привет, {{user_name}}!",
            message_kz="Сәлем, {{user_name}}!",
            scheduled_at=timezone.now() - timedelta(minutes=5),
            status="scheduled"
        )

        # Dispatch check task
        check_scheduled_mailings()

        # Reload task to verify it ran
        task.refresh_from_db()
        self.assertEqual(task.status, 'done')
        self.assertEqual(task.total_recipients, 2)
        self.assertEqual(task.sent_success, 2)
        self.assertEqual(task.failed_count, 0)
