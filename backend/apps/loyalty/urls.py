from django.urls import path
from apps.loyalty.views import (
    TmaAuthView, 
    CustomerMeView, 
    CustomerSyncView, 
    TmaWebhookView, 
    OrgCustomerViewSet, 
    CustomerGoogleWalletLinkView,
    LoyaltyProgramViewSet
)

urlpatterns = [
    path('tma/auth/', TmaAuthView.as_view(), name='tma_auth'),
    path('customer/me/', CustomerMeView.as_view(), name='customer_me'),
    path('customer/sync/', CustomerSyncView.as_view(), name='customer_sync'),
    path('webhook/<int:org_id>/<str:bot_token>/', TmaWebhookView.as_view(), name='tma_webhook'),
    
    path('customer/wallet/google/', CustomerGoogleWalletLinkView.as_view(), name='customer_wallet_google'),
    
    # Organization customer database
    path('organizations/<int:organization_id>/customers/', OrgCustomerViewSet.as_view({'get': 'list'}), name='org_customers'),

    # Organization loyalty programs list/detail
    path('organizations/<int:organization_id>/loyalty-programs/', LoyaltyProgramViewSet.as_view({'get': 'list', 'post': 'create'}), name='org_loyalty_programs'),
    path('organizations/<int:organization_id>/loyalty-programs/<int:pk>/', LoyaltyProgramViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='org_loyalty_program_detail'),
]
