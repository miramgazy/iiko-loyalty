from django.test import TestCase
from rest_framework.test import APIClient
from apps.core.models import Organization
from apps.loyalty.models import Customer
from apps.loyalty.views_utils import validate_tg_init_data
from unittest.mock import patch
import urllib.parse
import hmac
import hashlib
import json
import time

@patch('apps.loyalty.tasks.requests.post')
class LoyaltyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.core.cache import cache
        cache.clear()
        self.organization = Organization.objects.create(
            name="Pizza Place",
            slug="pizza-place",
            tg_bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            tg_bot_username="pizza_bot",
            tma_name="loyalty"
        )

    def test_tg_init_data_validation(self, mock_post):
        bot_token = self.organization.tg_bot_token
        user_dict = {
            "id": 55555,
            "first_name": "Bob",
            "last_name": "Smith",
            "username": "bobsmith"
        }
        auth_date = int(time.time())
        
        params = {
            "auth_date": str(auth_date),
            "query_id": "AAH55555AAAAA",
            "user": json.dumps(user_dict)
        }
        
        sorted_params = sorted(params.items())
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_params])
        
        secret_key = hmac.new(b"WebAppData", bot_token.encode('utf-8'), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
        
        params["hash"] = calculated_hash
        init_data = urllib.parse.urlencode(params)
        
        extracted_user = validate_tg_init_data(init_data, bot_token)
        self.assertEqual(extracted_user["id"], 55555)
        self.assertEqual(extracted_user["first_name"], "Bob")

        res = self.client.post('/api/loyalty/tma/auth/', {
            'initData': init_data,
            'bot_username': 'pizza_bot'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)
        self.assertEqual(res.data['customer']['phone'], None)
        self.assertEqual(res.data['customer']['is_onboarded'], False)

        customer = Customer.objects.get(telegram_id=55555)
        self.assertEqual(customer.first_name, "Bob")
        self.assertEqual(customer.last_name, "Smith")

    def test_iiko_webhook_deduplication(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}

        # Set organization iiko ID
        self.organization.iiko_organization_id = '03bf0000-6bec-ac1f-afb6-08deb71576ad'
        self.organization.save()

        # Pre-create customer to trigger telegram push sending
        Customer.objects.create(
            organization=self.organization,
            iiko_customer_id='03bf0000-6bec-ac1f-4a7b-08deb71de88a',
            telegram_id=99999,
            is_bot_subscribed=True
        )

        from apps.loyalty.models import IikoWebhookLog
        from apps.loyalty.tasks import process_iiko_webhook

        # Create two webhook logs with the same transactionId
        payload = {
            'transactionId': 'test-tx-123',
            'customerId': '03bf0000-6bec-ac1f-4a7b-08deb71de88a',
            'organizationId': '03bf0000-6bec-ac1f-afb6-08deb71576ad',
            'balance': 100,
            'sum': 10
        }
        
        log1 = IikoWebhookLog.objects.create(
            organization_id=payload['organizationId'],
            event_type='RefillWallet',
            payload=payload,
            status='PENDING'
        )
        
        log2 = IikoWebhookLog.objects.create(
            organization_id=payload['organizationId'],
            event_type='RefillWallet',
            payload=payload,
            status='PENDING'
        )

        # Process first webhook
        mock_post.reset_mock()
        process_iiko_webhook(log1.id)
        log1.refresh_from_db()
        self.assertEqual(log1.status, 'SUCCESS')
        
        # Verify first one sent a message (mock_post called)
        mock_post.assert_called_once()
        
        # Reset mock
        mock_post.reset_mock()

        # Process second webhook (should be deduplicated)
        process_iiko_webhook(log2.id)
        log2.refresh_from_db()
        
        # Should be set to SUCCESS but deduplicated (no requests.post call)
        self.assertEqual(log2.status, 'SUCCESS')
        self.assertIn("Deduplicated", log2.error_message)
        mock_post.assert_not_called()

    @patch('apps.loyalty.tasks.sync_customer_to_iiko.delay')
    def test_iiko_non_wallet_webhooks(self, mock_sync_delay, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}

        # Set organization iiko ID
        self.organization.iiko_organization_id = '03bf0000-6bec-ac1f-afb6-08deb71576ad'
        self.organization.save()

        # Pre-create customer to trigger telegram push sending
        customer = Customer.objects.create(
            organization=self.organization,
            iiko_customer_id='03bf0000-6bec-ac1f-4a7b-08deb71de88a',
            telegram_id=99999,
            is_bot_subscribed=True,
            loyalty_balance=150
        )

        from apps.loyalty.models import IikoWebhookLog
        from apps.loyalty.tasks import process_iiko_webhook

        # 1. Test InclusionInProgram
        log_inclusion = IikoWebhookLog.objects.create(
            organization_id='03bf0000-6bec-ac1f-afb6-08deb71576ad',
            event_type='InclusionInProgram',
            payload={
                'customerId': '03bf0000-6bec-ac1f-4a7b-08deb71de88a',
                'organizationId': '03bf0000-6bec-ac1f-afb6-08deb71576ad',
                'notificationType': 4
            },
            status='PENDING'
        )

        # Reset mocks right before calling webhook
        mock_post.reset_mock()
        mock_sync_delay.reset_mock()
        process_iiko_webhook(log_inclusion.id)
        
        # Verify balance remains unchanged (not set to 0)
        customer.refresh_from_db()
        self.assertEqual(customer.loyalty_balance, 150)
        # Verify sync was triggered
        mock_sync_delay.assert_called_once_with(customer.id, push=False)
        # Verify custom Telegram welcome message was sent
        mock_post.assert_called_once()
        self.assertIn("Добро пожаловать", mock_post.call_args[1]['json']['text'])

        # 2. Test MagnetCardChanged
        log_card = IikoWebhookLog.objects.create(
            organization_id='03bf0000-6bec-ac1f-afb6-08deb71576ad',
            event_type='MagnetCardChanged',
            payload={
                'customerId': '03bf0000-6bec-ac1f-4a7b-08deb71de88a',
                'organizationId': '03bf0000-6bec-ac1f-afb6-08deb71576ad',
                'notificationType': 3,
                'number': '999888777'
            },
            status='PENDING'
        )

        # Reset mocks right before calling webhook
        mock_post.reset_mock()
        mock_sync_delay.reset_mock()
        process_iiko_webhook(log_card.id)
        
        customer.refresh_from_db()
        # Verify card number was updated in DB
        self.assertEqual(customer.iiko_card_number, '999888777')
        # Verify balance remains unchanged (not set to 0)
        self.assertEqual(customer.loyalty_balance, 150)
        # Verify sync was triggered
        mock_sync_delay.assert_called_once_with(customer.id, push=False)
        # Verify Telegram card issue message was sent
        mock_post.assert_called_once()
        self.assertIn("выпущена виртуальная карта лояльности", mock_post.call_args[1]['json']['text'])

        # 3. Test SimplePush
        log_push = IikoWebhookLog.objects.create(
            organization_id='03bf0000-6bec-ac1f-afb6-08deb71576ad',
            event_type='SimplePush',
            payload={
                'customerId': '03bf0000-6bec-ac1f-4a7b-08deb71de88a',
                'organizationId': '03bf0000-6bec-ac1f-afb6-08deb71576ad',
                'notificationType': 5,
                'text': 'Hello from iiko push!'
            },
            status='PENDING'
        )

        # Reset mocks right before calling webhook
        mock_post.reset_mock()
        mock_sync_delay.reset_mock()
        process_iiko_webhook(log_push.id)

        customer.refresh_from_db()
        self.assertEqual(customer.loyalty_balance, 150)
        mock_sync_delay.assert_called_once_with(customer.id, push=False)
        # Verify exact SimplePush text was forwarded
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args[1]['json']['text'], 'Hello from iiko push!')

    @patch('apps.loyalty.tasks.IikoLoyaltyService')
    def test_customer_wallets_sync_and_webhook(self, mock_service_class, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}

        # Set organization iiko ID
        self.organization.iiko_organization_id = '03bf0000-6bec-ac1f-afb6-08deb71576ad'
        self.organization.save()

        # Create customer
        customer = Customer.objects.create(
            organization=self.organization,
            iiko_customer_id='03bf0000-6bec-ac1f-4a7b-08deb71de88a',
            telegram_id=99999,
            is_bot_subscribed=True,
            phone='+77779285899',
            loyalty_balance=0
        )

        # Mock the iiko service responses
        mock_service = mock_service_class.return_value
        mock_service.get_customer_info_by_id.return_value = {
            "id": str(customer.iiko_customer_id),
            "name": "Bob",
            "walletBalances": [
                {
                    "id": "11111111-2222-3333-4444-555555555555",
                    "name": "Накопительный",
                    "type": 1,
                    "balance": 120.0
                },
                {
                    "id": "66666666-7777-8888-9999-000000000000",
                    "name": "Подарочный",
                    "type": 1,
                    "balance": 50.0
                },
                {
                    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "name": "Депозит",
                    "type": 2,
                    "balance": 1000.0
                }
            ]
        }

        # Call sync
        from apps.loyalty.tasks import sync_customer_to_iiko
        sync_customer_to_iiko(customer.id)

        customer.refresh_from_db()
        # Verify overall active balance is sum of type 1 wallets: 120 + 50 = 170
        self.assertEqual(customer.loyalty_balance, 170)

        # Verify all wallets created in DB
        from apps.loyalty.models import CustomerWallet
        self.assertEqual(CustomerWallet.objects.filter(customer=customer).count(), 3)
        
        w1 = CustomerWallet.objects.get(customer=customer, wallet_id="11111111-2222-3333-4444-555555555555")
        self.assertEqual(w1.name, "Накопительный")
        self.assertEqual(w1.balance, 120.0)

        w2 = CustomerWallet.objects.get(customer=customer, wallet_id="66666666-7777-8888-9999-000000000000")
        self.assertEqual(w2.name, "Подарочный")
        self.assertEqual(w2.balance, 50.0)

        # Test webhook updating a specific wallet
        from apps.loyalty.models import IikoWebhookLog
        from apps.loyalty.tasks import process_iiko_webhook

        log_refill = IikoWebhookLog.objects.create(
            organization_id='03bf0000-6bec-ac1f-afb6-08deb71576ad',
            event_type='RefillWallet',
            payload={
                'customerId': str(customer.iiko_customer_id),
                'organizationId': '03bf0000-6bec-ac1f-afb6-08deb71576ad',
                'walletId': "11111111-2222-3333-4444-555555555555",
                'balance': 200.0, # changed from 120 to 200
                'sum': 80.0,
                'notificationType': 1
            },
            status='PENDING'
        )

        mock_post.reset_mock()
        process_iiko_webhook(log_refill.id)

        # Verify wallet 1 balance is updated
        w1.refresh_from_db()
        self.assertEqual(w1.balance, 200.0)

        # Verify overall customer balance is updated (200 + 50 = 250)
        customer.refresh_from_db()
        self.assertEqual(customer.loyalty_balance, 250)

        # Verify Telegram message was sent
        mock_post.assert_called_once()
        self.assertIn("Вам начислено 80.0", mock_post.call_args[1]['json']['text'])
