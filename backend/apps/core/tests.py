from django.test import TestCase
from django.conf import settings
from apps.core.utils import normalize_phone
from apps.core.models import Organization

from unittest.mock import patch

class CoreUtilsTests(TestCase):
    def test_normalize_phone(self):
        self.assertEqual(normalize_phone("87011112233"), "+77011112233")
        self.assertEqual(normalize_phone("+7 (701) 111-22-33"), "+77011112233")
        self.assertEqual(normalize_phone("77011112233"), "+77011112233")
        self.assertEqual(normalize_phone("7011112233"), "+77011112233")
        self.assertEqual(normalize_phone(None), "")
        self.assertEqual(normalize_phone(""), "")

@patch('apps.loyalty.tasks.requests.post')
class CoreEncryptionTests(TestCase):
    def test_organization_encryption(self, mock_post):
        org = Organization.objects.create(
            name="Test Cafe",
            slug="test-cafe",
            tg_bot_token="plain_bot_token_123",
            tg_bot_username="test_cafe_bot",
            iiko_api_login="plain_iiko_login_456"
        )
        
        reloaded = Organization.objects.get(id=org.id)
        
        self.assertEqual(reloaded.tg_bot_token, "plain_bot_token_123")
        self.assertEqual(reloaded.iiko_api_login, "plain_iiko_login_456")
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT tg_bot_token, iiko_api_login FROM core_organization WHERE id = %s", [org.id])
            row = cursor.fetchone()
            db_tg_bot_token = row[0]
            db_iiko_api_login = row[1]
            
            self.assertNotEqual(db_tg_bot_token, "plain_bot_token_123")
            self.assertNotEqual(db_iiko_api_login, "plain_iiko_login_456")
            self.assertTrue(db_tg_bot_token.startswith("gAAAAA"))
            self.assertTrue(db_iiko_api_login.startswith("gAAAAA"))


from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.accounts.models import UserOrganization
from apps.loyalty.models import Customer
from rest_framework_simplejwt.tokens import RefreshToken
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

@patch('apps.loyalty.tasks.requests.post')
class CoreViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_user = User.objects.create_superuser(
            username="superuser",
            email="superuser@example.com",
            password="superuserpass"
        )
        self.org_manager = User.objects.create_user(
            username="orgmanager",
            email="manager@example.com",
            password="managerpass",
            is_staff=True
        )
        self.org_admin = User.objects.create_user(
            username="orgadmin",
            email="admin@example.com",
            password="adminpass",
            is_staff=True
        )
        self.organization = Organization.objects.create(
            name="Pizza Palace",
            slug="pizza-place",
            tg_bot_token="bot_palace_123",
            tg_bot_username="pizza_bot",
            tma_name="loyalty"
        )
        
        # Link manager and admin
        UserOrganization.objects.create(
            user=self.org_manager,
            organization=self.organization,
            role=UserOrganization.ROLE_ORG_MANAGER
        )
        UserOrganization.objects.create(
            user=self.org_admin,
            organization=self.organization,
            role=UserOrganization.ROLE_ORG_ADMIN
        )

    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        refresh['user_type'] = 'employee'
        return str(refresh.access_token)

    def test_superadmin_organization_api(self, mock_post):
        # Authenticate as non-superuser
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.org_manager)}')
        res = self.client.get('/api/core/organizations/')
        self.assertEqual(res.status_code, 403) # Forbidden
        
        # Authenticate as superuser
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.super_user)}')
        res = self.client.get('/api/core/organizations/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        
        # Create new organization
        res = self.client.post('/api/core/organizations/', {
            'name': 'New Burger',
            'slug': 'new-burger',
            'owner_email': 'newowner@example.com'
        })
        self.assertEqual(res.status_code, 201)
        self.assertIn('temp_password', res.data)
        
        # Check that owner is created
        owner_exists = User.objects.filter(email='newowner@example.com').exists()
        self.assertTrue(owner_exists)
        owner = User.objects.get(email='newowner@example.com')
        self.assertTrue(UserOrganization.objects.filter(user=owner, role=UserOrganization.ROLE_ORG_MANAGER).exists())

    def test_organization_settings_api(self, mock_post):
        # Get settings as OrgManager
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.org_manager)}')
        res = self.client.get(f'/api/core/organizations/{self.organization.id}/settings/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['name'], "Pizza Palace")
        
        # Update settings
        res = self.client.patch(f'/api/core/organizations/{self.organization.id}/settings/', {
            'name': 'Pizza Palace Updated',
            'branding': {'design_color': '#112233', 'greeting_text': 'Hello'}
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['name'], 'Pizza Palace Updated')
        self.assertEqual(res.data['branding']['design_color'], '#112233')

    def test_organization_logo_upload(self, mock_post):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.org_manager)}')
        
        # Simple text file (should fail)
        invalid_file = SimpleUploadedFile("logo.txt", b"plain text", content_type="text/plain")
        res = self.client.post(
            f'/api/core/organizations/{self.organization.id}/upload-logo/', 
            {'logo': invalid_file}, 
            format='multipart'
        )
        self.assertEqual(res.status_code, 400)
        
        # Fake PNG file (should pass)
        png_file = SimpleUploadedFile("logo.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
        res = self.client.post(
            f'/api/core/organizations/{self.organization.id}/upload-logo/', 
            {'logo': png_file}, 
            format='multipart'
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('logo_url', res.data)
        
        # Reload organization and verify branding logo_url
        org = Organization.objects.get(id=self.organization.id)
        self.assertEqual(org.branding['logo_url'], res.data['logo_url'])

    def test_employee_management(self, mock_post):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.org_manager)}')
        
        # List employees
        res = self.client.get(f'/api/accounts/organizations/{self.organization.id}/employees/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2) # manager & admin
        
        # Invite employee
        res = self.client.post(f'/api/accounts/organizations/{self.organization.id}/employees/', {
            'email': 'newemp@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'org_admin'
        })
        self.assertEqual(res.status_code, 201)
        self.assertIn('temp_password', res.data)
        self.assertEqual(res.data['role'], 'org_admin')
        
        new_emp = User.objects.get(email='newemp@example.com')
        
        # Remove employee (admin)
        res = self.client.delete(f'/api/accounts/organizations/{self.organization.id}/employees/{self.org_admin.id}/')
        self.assertEqual(res.status_code, 204)
        
        # Verify employee removed from org (membership deleted)
        self.assertFalse(UserOrganization.objects.filter(user=self.org_admin, organization=self.organization).exists())

    def test_customer_list_and_search(self, mock_post):
        # Create some customers
        c1 = Customer.objects.create(organization=self.organization, telegram_id=111, first_name="Alice", last_name="Smith", phone="+77011110001")
        c2 = Customer.objects.create(organization=self.organization, telegram_id=222, first_name="Bob", last_name="Jones", phone="+77011110002")
        
        # Authenticate as OrgAdmin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.org_admin)}')
        res = self.client.get(f'/api/loyalty/organizations/{self.organization.id}/customers/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        
        # Search by name
        res = self.client.get(f'/api/loyalty/organizations/{self.organization.id}/customers/', {'search': 'Alice'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['first_name'], 'Alice')

    @patch('requests.post')
    def test_send_test_message_api(self, mock_requests_post, mock_tasks_post):
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = {"ok": True, "result": {"message_id": 123}}

        # Authenticate as OrgManager
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token(self.org_manager)}')
        
        # Call send-test-message
        res = self.client.post(f'/api/core/organizations/{self.organization.id}/send-test-message/', {
            'telegram_id': '12345'
        }, format='json')
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'success')

        # Verify telegram_id is updated in profile
        self.org_manager.refresh_from_db()
        self.assertEqual(self.org_manager.telegram_id, 12345)

