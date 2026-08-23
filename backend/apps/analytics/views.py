from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.utils import timezone
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
            target_date = timezone.localdate()
            
        kpis = get_dashboard_kpis(org, target_date)
        return Response(kpis)


class OlapSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def post(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        
        if not org.is_analytics_enabled:
            return Response({"error": "Модуль аналитики отключен для этой организации"}, status=status.HTTP_403_FORBIDDEN)
            
        days = request.data.get('days', 7)
        if not isinstance(days, int) or days <= 0 or days > 30:
            return Response({"error": "Количество дней должно быть от 1 до 30"}, status=status.HTTP_400_BAD_REQUEST)
            
        report_type = request.data.get('report_type', 'kpi')
        if report_type not in ['kpi', 'payments', 'waiters', 'foodcost']:
            return Response({"error": "Неверный тип отчета"}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.analytics.services import (
            sync_daily_olap_for_date,
            sync_hourly_olap_for_date,
            sync_payment_types_olap_for_date,
            sync_waiters_olap_for_date
        )
        from datetime import date, timedelta
        
        today = timezone.localdate()
        success_count = 0
        error_count = 0
        last_error = None
        
        for i in range(days):
            target_date = today - timedelta(days=i)
            try:
                if report_type == 'kpi':
                    sync_daily_olap_for_date(org, target_date)
                    sync_hourly_olap_for_date(org, target_date)
                elif report_type == 'payments':
                    sync_payment_types_olap_for_date(org, target_date)
                elif report_type == 'waiters':
                    sync_waiters_olap_for_date(org, target_date)
                elif report_type == 'foodcost':
                    from apps.analytics.food_cost_service import sync_theoretical_food_cost, take_stock_snapshot, calculate_actual_food_cost
                    from apps.analytics.models import ProductStockSnapshot
                    sync_theoretical_food_cost(org, target_date)
                    if target_date == timezone.localdate():
                        take_stock_snapshot(org, target_date)
                    # Trigger actual food cost calculation if we have enough snapshots
                    snapshot_dates = sorted(
                        list(ProductStockSnapshot.objects.filter(organization=org).values_list('date', flat=True).distinct())
                    )
                    if len(snapshot_dates) >= 2:
                        start_date = snapshot_dates[-2]
                        end_date = snapshot_dates[-1]
                        calculate_actual_food_cost(org, start_date, end_date)
                success_count += 1
            except Exception as e:
                error_count += 1
                last_error = str(e)
                
        if error_count == days:
            return Response({
                "success": False,
                "error": f"Ошибка обновления: {last_error or 'проверьте настройки подключения к iiko'}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response({
            "success": True,
            "message": f"Синхронизация завершена. Успешно обновлено дней: {success_count}. Ошибок: {error_count}."
        })


class FoodCostReportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        if not org.is_analytics_enabled:
            return Response({"error": "Module 'analytics' is not enabled for this organization"}, status=status.HTTP_403_FORBIDDEN)
            
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = timezone.localdate()
            
        from apps.analytics.models import FoodCostReport
        # Get reports for categories on this date
        reports = FoodCostReport.objects.filter(organization=org, date=target_date)
        
        # Get historical data for the overall restaurant (last 30 days) to show trend
        from datetime import timedelta
        history_start = target_date - timedelta(days=30)
        history_reports = FoodCostReport.objects.filter(
            organization=org, 
            category_name="Все", 
            date__gte=history_start, 
            date__lte=target_date
        ).order_by('date')
        
        categories_data = []
        overall_data = None
        
        for r in reports:
            item = {
                "category_name": r.category_name,
                "revenue": float(r.revenue),
                "theoretical_cost": float(r.theoretical_cost),
                "theoretical_foodcost_percent": float(r.theoretical_foodcost_percent),
                "actual_cost": float(r.actual_cost) if r.actual_cost is not None else None,
                "actual_foodcost_percent": float(r.actual_foodcost_percent) if r.actual_foodcost_percent is not None else None,
                "variance_cost": float(r.variance_cost) if r.variance_cost is not None else None,
                "variance_percent": float(r.variance_percent) if r.variance_percent is not None else None,
            }
            if r.category_name == "Все":
                overall_data = item
            else:
                categories_data.append(item)
                
        history_data = []
        for r in history_reports:
            history_data.append({
                "date": r.date.strftime("%Y-%m-%d"),
                "theoretical_foodcost_percent": float(r.theoretical_foodcost_percent),
                "actual_foodcost_percent": float(r.actual_foodcost_percent) if r.actual_foodcost_percent is not None else None,
            })
            
        return Response({
            "date": target_date.strftime("%Y-%m-%d"),
            "categories": categories_data,
            "overall": overall_data,
            "history": history_data
        })



class PaymentTypeOlapView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        if not org.is_analytics_enabled:
            return Response({"error": "Module 'analytics' is not enabled for this organization"}, status=status.HTTP_403_FORBIDDEN)
            
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = timezone.localdate()
            
        from apps.analytics.models import PaymentTypeOlapReport
        reports = PaymentTypeOlapReport.objects.filter(organization=org, date=target_date)
        
        data = []
        for r in reports:
            data.append({
                "payment_type": r.payment_type,
                "revenue": float(r.revenue),
                "checks_count": r.checks_count
            })
            
        return Response(data)


class WaiterOlapView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        if not org.is_analytics_enabled:
            return Response({"error": "Module 'analytics' is not enabled for this organization"}, status=status.HTTP_403_FORBIDDEN)
            
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = timezone.localdate()
            
        from apps.analytics.models import WaiterOlapReport
        reports = WaiterOlapReport.objects.filter(organization=org, date=target_date).order_by('-revenue')
        
        data = []
        for r in reports:
            revenue = float(r.revenue)
            checks = r.checks_count
            avg_check = revenue / checks if checks > 0 else 0.0
            data.append({
                "waiter_name": r.waiter_name,
                "revenue": revenue,
                "checks_count": checks,
                "guests_count": r.guests_count,
                "avg_check": avg_check
            })
            
        return Response(data)


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
        IikoOlapPreset.objects.get_or_create(
            organization=org,
            report_type_key='payments',
            defaults={
                'name': 'Продажи по типам оплаты (Системный)',
                'description': 'Отчет по типам оплаты. Необходимые поля группировки: OpenDate.Typed, PayTypes. Агрегации: DishSumInt, UniqOrderId.',
                'preset_id': '00000000-0000-0000-0000-000000000000',
                'is_system': True
            }
        )
        IikoOlapPreset.objects.get_or_create(
            organization=org,
            report_type_key='waiters',
            defaults={
                'name': 'Продажи по официантам (Системный)',
                'description': 'Отчет по официантам. Необходимые поля группировки: OpenDate.Typed, WaiterName. Агрегации: DishSumInt, UniqOrderId, GuestNum.',
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

