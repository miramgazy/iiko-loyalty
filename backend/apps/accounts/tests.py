from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.models import Organization
from apps.loyalty.models import Customer
from apps.accounts.models import UserOrganization
from unittest.mock import patch

User = get_user_model()

@patch('apps.loyalty.tasks.requests.post')
class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="Burger Palace",
            slug="burger-palace",
            tg_bot_token="bot_palace_123",
            tg_bot_username="burger_palace_bot"
        )
        self.user = User.objects.create_user(
            username="manager1",
            email="manager1@example.com",
            phone="+77011112233",
            password="securepassword123",
            is_staff=True
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.organization,
            role=UserOrganization.ROLE_ORG_MANAGER
        )

    def test_multi_method_authentication(self, mock_post):
        # 1. Username
        res1 = self.client.post('/api/accounts/token/', {
            'username': 'manager1',
            'password': 'securepassword123'
        })
        self.assertEqual(res1.status_code, 200)
        self.assertIn('access', res1.data)
        self.assertIn('user', res1.data)
        self.assertEqual(res1.data['user']['username'], 'manager1')
        self.assertEqual(len(res1.data['user']['memberships']), 1)
        self.assertEqual(res1.data['user']['memberships'][0]['role'], 'org_manager')

        # 2. Email
        res2 = self.client.post('/api/accounts/token/', {
            'username': 'manager1@example.com',
            'password': 'securepassword123'
        })
        self.assertEqual(res2.status_code, 200)
        self.assertIn('access', res2.data)

        # 3. Phone
        res3 = self.client.post('/api/accounts/token/', {
            'username': '+7 (701) 111-22-33',
            'password': 'securepassword123'
        })
        self.assertEqual(res3.status_code, 200)
        self.assertIn('access', res3.data)

    def test_customer_jwt_authentication(self, mock_post):
        customer = Customer.objects.create(
            organization=self.organization,
            telegram_id=99999,
            phone="+77778889900",
            first_name="Alice",
            last_name="Green"
        )
        
        refresh = RefreshToken()
        refresh['user_id'] = customer.id
        refresh['user_type'] = 'customer'
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        res = self.client.get('/api/loyalty/customer/me/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['telegram_id'], 99999)
        self.assertEqual(res.data['first_name'], 'Alice')

    def test_superadmin_user_crud(self, mock_post):
        # Create a superuser and get token
        superuser = User.objects.create_superuser(
            username="admin_super",
            email="admin_super@example.com",
            password="adminpassword123"
        )
        refresh = RefreshToken.for_user(superuser)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 1. Create a manager
        create_res = self.client.post('/api/accounts/superadmin/users/', {
            'username': 'new_manager',
            'email': 'new_manager@example.com',
            'password': 'managerpassword123',
            'first_name': 'John',
            'last_name': 'Doe',
            'organization_id': self.organization.id
        })
        self.assertEqual(create_res.status_code, 201)
        self.assertEqual(create_res.data['username'], 'new_manager')
        
        new_manager_id = create_res.data['id']
        
        # Verify database link
        user = User.objects.get(id=new_manager_id)
        self.assertTrue(user.check_password('managerpassword123'))
        self.assertTrue(user.is_staff)
        self.assertEqual(user.memberships.count(), 1)
        self.assertEqual(user.memberships.first().organization, self.organization)
        self.assertEqual(user.memberships.first().role, UserOrganization.ROLE_ORG_MANAGER)
        
        # 2. List managers
        list_res = self.client.get('/api/accounts/superadmin/users/')
        self.assertEqual(list_res.status_code, 200)
        # Should include both self.user (which is org_manager) and new_manager
        self.assertEqual(len(list_res.data), 2)
        
        # 3. Update manager
        update_res = self.client.put(f'/api/accounts/superadmin/users/{new_manager_id}/', {
            'username': 'updated_manager',
            'email': 'new_manager@example.com',
            'first_name': 'Johnny',
            'last_name': 'Doe',
            'organization_id': self.organization.id,
            'password': 'newpassword123'
        })
        self.assertEqual(update_res.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.username, 'updated_manager')
        self.assertEqual(user.first_name, 'Johnny')
        self.assertTrue(user.check_password('newpassword123'))
        
        # 4. Delete manager
        delete_res = self.client.delete(f'/api/accounts/superadmin/users/{new_manager_id}/')
        self.assertEqual(delete_res.status_code, 204)
        self.assertFalse(User.objects.filter(id=new_manager_id).exists())

    def test_employee_custom_password(self, mock_post):
        # Login as self.user (org_manager)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Create employee with custom password
        res = self.client.post(f'/api/accounts/organizations/{self.organization.id}/employees/', {
            'email': 'emp_custom@example.com',
            'first_name': 'Bob',
            'last_name': 'Smith',
            'role': UserOrganization.ROLE_ORG_ADMIN,
            'password': 'bobpassword123'
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['email'], 'emp_custom@example.com')
        self.assertNotIn('temp_password', res.data)
        
        # Verify user password in DB
        user = User.objects.get(email='emp_custom@example.com')
        self.assertTrue(user.check_password('bobpassword123'))
        self.assertTrue(user.is_staff)


