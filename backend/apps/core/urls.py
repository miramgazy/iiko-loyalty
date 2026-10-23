from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import (
    SuperAdminOrganizationViewSet, OrganizationSettingsView, OrganizationLogoUploadView, OrganizationBannerUploadView,
    OrganizationOnboardingBannerUploadView, OrganizationWalletLogoUploadView,
    OrganizationGoogleWalletSettingsView, OrganizationWebhookStatusView, OrganizationSendTestMessageView,
    OrganizationTestIikoConnectionView, OrganizationTestIikoServerConnectionView, TmaEmployeeViewSet,
    OrganizationWabaTemplatesView, OrganizationWabaPhoneNumbersView, OrganizationWabaSendTestView,
    OrganizationWabaLogsView, OrganizationWabaRulesViewSet
)

router = DefaultRouter()
router.register(r'organizations', SuperAdminOrganizationViewSet, basename='superadmin_orgs')

urlpatterns = [
    # SuperAdmin endpoints (router holds /api/core/organizations/)
    path('', include(router.urls)),
    
    # Organization Manager endpoints
    path('organizations/<int:organization_id>/settings/', OrganizationSettingsView.as_view(), name='org_settings'),
    path('organizations/<int:organization_id>/upload-logo/', OrganizationLogoUploadView.as_view(), name='org_logo_upload'),
    path('organizations/<int:organization_id>/upload-wallet-logo/', OrganizationWalletLogoUploadView.as_view(), name='org_wallet_logo_upload'),
    path('organizations/<int:organization_id>/upload-banner/', OrganizationBannerUploadView.as_view(), name='org_banner_upload'),
    path('organizations/<int:organization_id>/upload-onboarding-banner/', OrganizationOnboardingBannerUploadView.as_view(), name='org_onboarding_banner_upload'),
    path('organizations/<int:organization_id>/google-wallet-class/', OrganizationGoogleWalletSettingsView.as_view(), name='org_google_wallet_class'),
    path('organizations/<int:organization_id>/webhook-status/', OrganizationWebhookStatusView.as_view(), name='org_webhook_status'),
    path('organizations/<int:organization_id>/send-test-message/', OrganizationSendTestMessageView.as_view(), name='org_send_test_message'),
    path('organizations/<int:organization_id>/test-iiko-connection/', OrganizationTestIikoConnectionView.as_view(), name='org_test_iiko_connection'),
    path('organizations/<int:organization_id>/test-iiko-server-connection/', OrganizationTestIikoServerConnectionView.as_view(), name='org_test_iiko_server_connection'),
    
    # WhatsApp WABA endpoints
    path('organizations/<int:organization_id>/waba/templates/', OrganizationWabaTemplatesView.as_view(), name='org_waba_templates'),
    path('organizations/<int:organization_id>/waba/phone-numbers/', OrganizationWabaPhoneNumbersView.as_view(), name='org_waba_phone_numbers'),
    path('organizations/<int:organization_id>/waba/send-test/', OrganizationWabaSendTestView.as_view(), name='org_waba_send_test'),
    path('organizations/<int:organization_id>/waba/logs/', OrganizationWabaLogsView.as_view(), name='org_waba_logs'),
    path('organizations/<int:organization_id>/waba/rules/', OrganizationWabaRulesViewSet.as_view({'get': 'list', 'post': 'create'}), name='org_waba_rules'),
    path('organizations/<int:organization_id>/waba/rules/<int:pk>/', OrganizationWabaRulesViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='org_waba_rule_detail'),

    # TMA Employees
    path('organizations/<int:organization_id>/tma-employees/', TmaEmployeeViewSet.as_view({'get': 'list', 'post': 'create'}), name='org_tma_employees'),
    path('organizations/<int:organization_id>/tma-employees/<int:pk>/', TmaEmployeeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='org_tma_employee_detail'),
]
