import logging
from datetime import date, timedelta
from config.celery import app
from apps.core.models import Organization
from apps.inventory.services import (
    sync_purchase_history, sync_stop_lists, check_min_max_limits
)

logger = logging.getLogger(__name__)

@app.task
def sync_all_organizations_inventory():
    """
    Syncs inventory stock levels and checks Min-Max rules.
    Runs every 15 minutes.
    """
    active_orgs = Organization.objects.filter(is_active=True, is_analytics_enabled=True)
    for org in active_orgs:
        try:
            # This fetches stock levels and triggers alerts
            check_min_max_limits(org)
        except Exception as e:
            logger.error(f"Failed to check stock limits for {org.name}: {e}")

@app.task
def sync_all_organizations_purchases():
    """
    Syncs purchase invoices history (Price Drift).
    Runs every 4 hours.
    """
    active_orgs = Organization.objects.filter(is_active=True, is_analytics_enabled=True)
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    for org in active_orgs:
        try:
            # Sync today and yesterday
            sync_purchase_history(org, yesterday)
            sync_purchase_history(org, today)
        except Exception as e:
            logger.error(f"Failed to sync purchases for {org.name}: {e}")

@app.task
def sync_all_organizations_stop_lists():
    """
    Syncs active stop lists and processes lost revenue.
    Runs every 10 minutes.
    """
    active_orgs = Organization.objects.filter(is_active=True, is_analytics_enabled=True)
    for org in active_orgs:
        try:
            sync_stop_lists(org)
        except Exception as e:
            logger.error(f"Failed to sync stop lists for {org.name}: {e}")
