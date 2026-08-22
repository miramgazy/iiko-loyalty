import logging
from datetime import date, timedelta
from django.utils import timezone
from config.celery import app
from apps.core.models import Organization
from apps.analytics.services import sync_daily_olap_for_date, sync_hourly_olap_for_date

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
        except Exception as e:
            logger.error(f"Failed to sync OLAP for {org.name} on {yesterday}: {e}")
            
        # Sync today to get current day-to-date metrics
        try:
            sync_daily_olap_for_date(org, today)
            sync_hourly_olap_for_date(org, today)
        except Exception as e:
            logger.error(f"Failed to sync OLAP for {org.name} on {today}: {e}")
