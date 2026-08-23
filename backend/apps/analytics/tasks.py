import logging
from datetime import date, timedelta
from django.utils import timezone
from config.celery import app
from apps.core.models import Organization
from apps.analytics.services import (
    sync_daily_olap_for_date,
    sync_hourly_olap_for_date,
    sync_payment_types_olap_for_date,
    sync_waiters_olap_for_date
)
from apps.analytics.food_cost_service import (
    sync_theoretical_food_cost,
    take_stock_snapshot,
    calculate_actual_food_cost
)
from apps.analytics.models import ProductStockSnapshot

logger = logging.getLogger(__name__)

@app.task
def sync_all_organizations_olap():
    """
    Periodic task to sync OLAP data for all organizations that have analytics module enabled.
    """
    active_orgs = Organization.objects.filter(is_active=True, is_analytics_enabled=True)
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    
    for org in active_orgs:
        # Sync yesterday to finalize numbers
        try:
            sync_daily_olap_for_date(org, yesterday)
            sync_hourly_olap_for_date(org, yesterday)
            sync_payment_types_olap_for_date(org, yesterday)
            sync_waiters_olap_for_date(org, yesterday)
        except Exception as e:
            logger.error(f"Failed to sync OLAP for {org.name} on {yesterday}: {e}")
            
        # Sync today to get current day-to-date metrics
        try:
            sync_daily_olap_for_date(org, today)
            sync_hourly_olap_for_date(org, today)
            sync_payment_types_olap_for_date(org, today)
            sync_waiters_olap_for_date(org, today)
        except Exception as e:
            logger.error(f"Failed to sync OLAP for {org.name} on {today}: {e}")

@app.task
def sync_all_organizations_food_cost():
    """
    Periodic task to sync theoretical food cost, take daily stock level snapshots,
    and calculate actual food cost for completed inventory periods.
    """
    active_orgs = Organization.objects.filter(is_active=True, is_analytics_enabled=True)
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    
    for org in active_orgs:
        # 1. Sync theoretical food cost
        try:
            sync_theoretical_food_cost(org, yesterday)
            sync_theoretical_food_cost(org, today)
        except Exception as e:
            logger.error(f"Failed to sync theoretical food cost for {org.name} on {today}: {e}")
            
        # 2. Take daily stock balance snapshot
        try:
            take_stock_snapshot(org, today)
        except Exception as e:
            logger.error(f"Failed to take stock snapshot for {org.name} on {today}: {e}")
            
        # 3. Calculate actual food cost for the latest completed inventory interval
        try:
            snapshot_dates = sorted(
                list(ProductStockSnapshot.objects.filter(organization=org).values_list('date', flat=True).distinct())
            )
            if len(snapshot_dates) >= 2:
                start_date = snapshot_dates[-2]
                end_date = snapshot_dates[-1]
                calculate_actual_food_cost(org, start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to calculate actual food cost for {org.name} on {today}: {e}")

