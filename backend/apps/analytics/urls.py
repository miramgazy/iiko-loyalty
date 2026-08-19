from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.analytics.views import DashboardKpiView, IikoOlapPresetViewSet

router = DefaultRouter()
router.register(r'organizations/(?P<organization_id>\d+)/presets', IikoOlapPresetViewSet, basename='olap_presets')

urlpatterns = [
    path('', include(router.urls)),
    path('organizations/<int:organization_id>/kpi/', DashboardKpiView.as_view(), name='dashboard_kpi'),
]
