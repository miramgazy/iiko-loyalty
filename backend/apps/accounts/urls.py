from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import EmployeeTokenView, EmployeeViewSet, TmaWebhookView, SuperAdminUserViewSet

urlpatterns = [
    path('token/', EmployeeTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # TMA Webhook for command and callback query consents
    path('tma/webhook/<slug:org_slug>/<str:token>/', TmaWebhookView.as_view(), name='tma_webhook_consent'),
    
    # Employee management endpoints
    path('organizations/<int:organization_id>/employees/', EmployeeViewSet.as_view({'get': 'list', 'post': 'create'}), name='org_employees'),
    path('organizations/<int:organization_id>/employees/<int:pk>/', EmployeeViewSet.as_view({'delete': 'destroy'}), name='org_employee_delete'),

    # SuperAdmin User management
    path('superadmin/users/', SuperAdminUserViewSet.as_view({'get': 'list', 'post': 'create'}), name='superadmin_users'),
    path('superadmin/users/<int:pk>/', SuperAdminUserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='superadmin_user_detail'),
]

