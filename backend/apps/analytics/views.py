from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets
from django.shortcuts import get_object_or_404
from datetime import datetime
from apps.core.models import Organization
from apps.accounts.permissions import IsOrgEmployee
from apps.analytics.services import get_dashboard_kpis
from apps.analytics.models import IikoOlapPreset
from apps.analytics.serializers import IikoOlapPresetSerializer

class DashboardKpiView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        
        # Check module availability
        if not org.is_analytics_enabled:
            return Response({"error": "Module 'analytics' is not enabled for this organization"}, status=status.HTTP_403_FORBIDDEN)
            
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = datetime.today().date()
            
        kpis = get_dashboard_kpis(org, target_date)
        return Response(kpis)


class IikoOlapPresetViewSet(viewsets.ModelViewSet):
    serializer_class = IikoOlapPresetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get_queryset(self):
        org_id = self.kwargs.get('organization_id')
        org = get_object_or_404(Organization, id=org_id)
        
        # Seed system presets if they don't exist
        IikoOlapPreset.objects.get_or_create(
            organization=org,
            report_type_key='daily_kpi',
            defaults={
                'name': 'Дневные продажи для KPI (Системный)',
                'description': 'Дневной отчет. Необходимые поля группировки: OpenDate.Typed. Агрегации: DishSumInt, DishCost.ProductCost, DishDiscountSumInt, ChecksCount, GuestNum.',
                'preset_id': '00000000-0000-0000-0000-000000000000',
                'is_system': True
            }
        )
        IikoOlapPreset.objects.get_or_create(
            organization=org,
            report_type_key='hourly_sales',
            defaults={
                'name': 'Почасовые продажи блюд (Системный)',
                'description': 'Почасовой отчет. Необходимые поля группировки: OpenDate.Typed, Hour, DishId, DishName. Агрегации: DishQty, DishSumInt.',
                'preset_id': '00000000-0000-0000-0000-000000000000',
                'is_system': True
            }
        )
        
        return IikoOlapPreset.objects.filter(organization=org).order_by('-is_system', 'name')

    def perform_create(self, serializer):
        org_id = self.kwargs.get('organization_id')
        org = get_object_or_404(Organization, id=org_id)
        serializer.save(organization=org, report_type_key='custom', is_system=False)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_system:
            return Response({"error": "Системные отчеты нельзя удалять."}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

