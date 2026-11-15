from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.invoices.views import (
    InvoiceUploadView, InvoiceViewSet, IikoStoresView,
    IikoSuppliersView, IikoProductsCatalogView,
    SupplierProductAliasViewSet, TestVisionConnectionView
)

router = DefaultRouter()
router.register(r'documents', InvoiceViewSet, basename='invoice')
router.register(r'knowledge-base', SupplierProductAliasViewSet, basename='knowledge-base')

urlpatterns = [
    path('upload/', InvoiceUploadView.as_view(), name='invoice-upload'),
    path('stores/', IikoStoresView.as_view(), name='invoice-stores'),
    path('suppliers/', IikoSuppliersView.as_view(), name='invoice-suppliers'),
    path('products-catalog/', IikoProductsCatalogView.as_view(), name='invoice-products-catalog'),
    path('test-vision/', TestVisionConnectionView.as_view(), name='invoice-test-vision'),
    path('', include(router.urls)),
]
