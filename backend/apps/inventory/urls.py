from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.inventory.views import (
    ProductInventoryRuleViewSet, PurchaseOrderViewSet,
    PriceDriftListView, StopListHistoryListView, ApprovePurchaseOrderView
)

router = DefaultRouter()
router.register(r'organizations/(?P<organization_id>\d+)/rules', ProductInventoryRuleViewSet, basename='inventory_rules')
router.register(r'organizations/(?P<organization_id>\d+)/orders', PurchaseOrderViewSet, basename='purchase_orders')

urlpatterns = [
    path('', include(router.urls)),
    path('organizations/<int:organization_id>/price-drift/', PriceDriftListView.as_view(), name='price_drift'),
    path('organizations/<int:organization_id>/stop-lists/', StopListHistoryListView.as_view(), name='stop_lists'),
    path('organizations/<int:organization_id>/orders/<int:pk>/approve/', ApprovePurchaseOrderView.as_view(), name='approve_order'),
]
