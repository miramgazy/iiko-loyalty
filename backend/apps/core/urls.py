from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import (
    SuperAdminOrganizationViewSet, OrganizationSettingsView, OrganizationLogoUploadView,
    OrganizationGoogleWalletSettingsView, OrganizationWebhookStatusView, OrganizationSendTestMessageView
)

router = DefaultRouter()
router.register(r'organizations', SuperAdminOrganizationViewSet, basename='superadmin_orgs')

urlpatterns = [
    # SuperAdmin endpoints (router holds /api/core/organizations/)
    path('', include(router.urls)),
    
    # Organization Manager endpoints
    path('organizations/<int:organization_id>/settings/', OrganizationSettingsView.as_view(), name='org_settings'),
    path('organizations/<int:organization_id>/upload-logo/', OrganizationLogoUploadView.as_view(), name='org_logo_upload'),
    path('organizations/<int:organization_id>/google-wallet-class/', OrganizationGoogleWalletSettingsView.as_view(), name='org_google_wallet_class'),
    path('organizations/<int:organization_id>/webhook-status/', OrganizationWebhookStatusView.as_view(), name='org_webhook_status'),
    path('organizations/<int:organization_id>/send-test-message/', OrganizationSendTestMessageView.as_view(), name='org_send_test_message'),
]
