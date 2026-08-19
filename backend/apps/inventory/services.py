import httpx
import logging
import requests
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db.models import Avg, Sum
from django.conf import settings
from apps.core.models import Organization
from apps.loyalty.services import IikoAuthService
from apps.analytics.models import HourlyOlapReport
from apps.inventory.models import (
    ProductPurchaseHistory, StopListHistory,
    ProductInventoryRule, PurchaseOrder, PurchaseOrderItem
)

logger = logging.getLogger(__name__)

class IikoInventoryService:
    def __init__(self, organization: Organization):
        self.org = organization
        self.auth_service = IikoAuthService(organization)

    def _get_headers(self) -> dict:
        token = self.auth_service.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _get_api_url(self, endpoint: str) -> str:
        base = self.org.iiko_api_base_url.rstrip('/')
        if '/api/v2' in base:
            base = base.replace('/api/v2', '/api/1')
        elif '/api/2' in base:
            base = base.replace('/api/2', '/api/1')
        return f"{base}{endpoint}"

    def fetch_incoming_invoices(self, from_date: date, to_date: date) -> list:
        """
        Retrieves incoming invoices from iiko within dates.
        """
        url = self._get_api_url("/documents/incoming_invoice/by_dates")
        payload = {
            "organizationIds": [str(self.org.iiko_organization_id)],
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d")
        }
        
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                return response.json().get("incomingInvoices", [])
        except Exception as e:
            logger.error(f"Error fetching incoming invoices from iiko for org {self.org.id}: {e}")
            return []

    def fetch_active_stop_list(self) -> list:
        """
        Retrieves active stop list items from iiko.
        """
        url = self._get_api_url("/stop_lists")
        payload = {
            "organizationIds": [str(self.org.iiko_organization_id)]
        }
        
        try:
            with httpx.Client(timeout=20) as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                
                # Format: stopLists: [{ organizationId, items: [{ productId, startedAt }] }]
                stop_lists = response.json().get("stopLists", [])
                if stop_lists:
                    return stop_lists[0].get("items", [])
                return []
        except Exception as e:
            logger.error(f"Error fetching active stop list for org {self.org.id}: {e}")
            return []

    def fetch_stock_balances(self) -> list:
        """
        Retrieves current stock levels for ingredients.
        """
        url = self._get_api_url("/storage/inventory")
        payload = {
            "organizationIds": [str(self.org.iiko_organization_id)]
        }
        
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                return response.json().get("inventoryBalances", [])
        except Exception as e:
            logger.error(f"Error fetching stock balances for org {self.org.id}: {e}")
            return []

    def create_purchase_order(self, order: PurchaseOrder) -> str:
        """
        Creates a purchase order document in iiko Cloud.
        """
        url = self._get_api_url("/documents/purchase_order")
        
        items_payload = []
        for item in order.items.all():
            items_payload.append({
                "productId": str(item.product_id),
                "amount": float(item.quantity),
                "price": float(item.price) if item.price else 0.0
            })
            
        payload = {
            "organizationId": str(self.org.iiko_organization_id),
            "document": {
                "documentNumber": f"PO-{order.id}",
                "date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                "supplierId": str(order.supplier_id) if order.supplier_id else None,
                "items": items_payload,
                "comment": "Автоматический заказ из аналитической платформы"
            }
        }
        
        with httpx.Client(timeout=30) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            res_data = response.json()
            return res_data.get("documentId") or res_data.get("id") or "iiko_mock_doc_id"


def sync_purchase_history(org: Organization, target_date: date):
    logger.info(f"Syncing purchase history for {org.name} on {target_date}")
    service = IikoInventoryService(org)
    invoices = service.fetch_incoming_invoices(target_date, target_date)
    
    for inv in invoices:
        supplier_id = inv.get("supplierId")
        supplier_name = inv.get("supplierName")
        items = inv.get("items", [])
        
        for item in items:
            product_id = item.get("productId")
            product_name = item.get("productName")
            price = item.get("price", 0.0)
            qty = item.get("amount", 0.0)
            
            if not product_id:
                continue
                
            # Log purchase history, check if already recorded
            ProductPurchaseHistory.objects.update_or_create(
                organization=org,
                product_id=product_id,
                price=price,
                date=target_date,
                defaults={
                    "product_name": product_name,
                    "supplier_id": supplier_id,
                    "supplier_name": supplier_name,
                    "quantity": qty
                }
            )


def sync_stop_lists(org: Organization):
    logger.info(f"Syncing stop lists snapshot for {org.name}")
    service = IikoInventoryService(org)
    active_items = service.fetch_active_stop_list()
    
    active_ids = set()
    for item in active_items:
        prod_id = item.get("productId")
        if not prod_id:
            continue
        active_ids.add(prod_id)
        
        # Check if active stop list item already tracked in DB
        history_record, created = StopListHistory.objects.get_or_create(
            organization=org,
            product_id=prod_id,
            ended_at__isnull=True,
            defaults={
                "product_name": item.get("productName", "Блюдо"),
                "started_at": datetime.fromisoformat(item["startedAt"].replace("Z", "+00:00")) if item.get("startedAt") else timezone.now()
            }
        )
        
    # Find all currently open stop-list records in DB that are NO LONGER in the active list
    ended_records = StopListHistory.objects.filter(
        organization=org,
        ended_at__isnull=True
    ).exclude(product_id__in=active_ids)
    
    for record in ended_records:
        record.ended_at = timezone.now()
        record.duration_seconds = int((record.ended_at - record.started_at).total_seconds())
        
        # Calculate lost demand metrics
        calculate_lost_revenue_for_stop_list(record)
        record.save()
        logger.info(f"Closed stop list for product {record.product_name}, duration: {record.duration_seconds} sec")


def calculate_lost_revenue_for_stop_list(record: StopListHistory):
    """
    Evaluates lost demand during the stop list interval using average historical sales in the same hours.
    """
    # 1. Determine hours of stop list
    start_time = record.started_at
    end_time = record.ended_at or timezone.now()
    
    duration_hours = (end_time - start_time).total_seconds() / 3600.0
    if duration_hours <= 0.05:
        return
        
    # Get the day of the week
    weekday = start_time.weekday()
    
    # 2. Get average historical hourly sales of this product on the same day of the week
    # Query HourlyOlapReport records for the same product, same weekday
    # Average the quantity sold per hour
    avg_sales = HourlyOlapReport.objects.filter(
        organization=record.organization,
        product_id=record.product_id,
        date__week_day=weekday + 2 # Django weekday starts with 1=Sunday, 2=Monday... (Postgres / SQL standard)
    ).values('hour').annotate(avg_qty=Avg('quantity'), avg_rev=Avg('revenue'))
    
    # Map hour -> avg_qty
    hour_stats = {item['hour']: (float(item['avg_qty']), float(item['avg_rev'])) for item in avg_sales}
    
    # Iterate over every hour within the stop-list interval and aggregate
    lost_revenue = 0.0
    lost_qty = 0.0
    
    current_hour_time = start_time
    while current_hour_time <= end_time:
        hour = current_hour_time.hour
        stats = hour_stats.get(hour, (0.0, 0.0))
        
        # Calculate overlap fraction in this hour
        # If start is 12:30 and end is 14:15:
        # hour 12 has 30 mins (0.5), hour 13 has 60 mins (1.0), hour 14 has 15 mins (0.25)
        overlap_start = max(current_hour_time.replace(minute=0, second=0, microsecond=0), start_time)
        overlap_end = min(current_hour_time.replace(minute=59, second=59, microsecond=999999), end_time)
        overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600.0
        
        lost_qty += stats[0] * overlap_hours
        lost_revenue += stats[1] * overlap_hours
        
        current_hour_time += timedelta(hours=1)
        
    record.lost_revenue = lost_revenue
    
    # Profit calculation (Lost Profit = Lost Revenue - Lost Cost)
    # We estimate based on average foodcost or previous margin
    # Let's assume average markup margin of 65% (foodcost 35%)
    record.lost_profit = lost_revenue * 0.65


def calculate_price_drift(org: Organization):
    """
    Computes inflation/price drift for ingredients.
    """
    rules = ProductInventoryRule.objects.filter(organization=org)
    drift_report = []
    
    for rule in rules:
        purchases = ProductPurchaseHistory.objects.filter(
            organization=org,
            product_id=rule.product_id
        ).order_by('-date', '-created_at')[:2]
        
        if len(purchases) < 2:
            continue
            
        latest = purchases[0]
        previous = purchases[1]
        
        price_diff = latest.price - previous.price
        if previous.price > 0:
            diff_pct = (price_diff / previous.price) * 100
        else:
            diff_pct = 0.0
            
        cost_impact = price_diff * latest.quantity
        
        drift_report.append({
            "product_id": rule.product_id,
            "product_name": rule.product_name,
            "price_old": float(previous.price),
            "price_new": float(latest.price),
            "diff_percent": float(diff_pct),
            "cost_impact": float(cost_impact),
            "last_purchase_date": latest.date,
            "supplier_name": latest.supplier_name
        })
        
    # Sort by cost impact descending (top negative impact or top подорожавшие)
    drift_report.sort(key=lambda x: x["cost_impact"], reverse=True)
    return drift_report[:10]


def check_min_max_limits(org: Organization):
    """
    Compares current stock with rules and sends Telegram alert to responsible employees.
    """
    service = IikoInventoryService(org)
    balances = service.fetch_stock_balances()
    
    # Map product_id -> balance
    stock_map = {}
    for bal in balances:
        prod_id = bal.get("productId")
        if prod_id:
            stock_map[prod_id] = float(bal.get("balance", 0.0))
            
    rules = ProductInventoryRule.objects.filter(organization=org)
    
    for rule in rules:
        prod_id = str(rule.product_id)
        current_stock = stock_map.get(prod_id)
        
        if current_stock is None:
            continue
            
        min_stock = float(rule.min_stock)
        
        if current_stock <= min_stock:
            # We must trigger alert!
            # Check if we already alerted in last 4 hours for this product to prevent spam
            from apps.core.models import Employee, AlertLog
            from django.contrib.auth import get_user_model
            
            # Find alert log
            recent_alert = AlertLog.objects.filter(
                organization=org,
                alert_type="min_stock",
                entity_id=rule.product_id,
                created_at__gte=timezone.now() - timedelta(hours=4)
            ).exists()
            
            if recent_alert:
                continue
                
            # Send notification
            alert_text = (
                f"⚠️ <b>Внимание! Низкий остаток сырья</b>\n\n"
                f"Товар: <b>{rule.product_name}</b>\n"
                f"Текущий остаток: <b>{current_stock}</b>\n"
                f"Минимальный порог: <b>{min_stock}</b>\n\n"
                f"Необходимо сформировать заказ поставщику."
            )
            
            # Find responsible employees by role
            employees = Employee.objects.filter(
                organization=org,
                role=rule.responsible_role,
                is_active=True,
                telegram_id__isnull=False
            )
            
            for emp in employees:
                # Add interactive button
                inline_keyboard = [
                    [{"text": "🛒 Сформировать заказ", "callback_data": f"create_order_{rule.product_id}"}]
                ]
                try:
                    send_telegram_notification(org.tg_bot_token, emp.telegram_id, alert_text, inline_keyboard)
                except Exception as e:
                    logger.error(f"Failed to send telegram alert to employee {emp.id}: {e}")
                    
            # Log alert
            AlertLog.objects.create(
                organization=org,
                alert_type="min_stock",
                entity_id=rule.product_id,
                message=alert_text
            )


def send_telegram_notification(bot_token: str, chat_id: int, text: str, inline_keyboard: list = None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if inline_keyboard:
        payload["reply_markup"] = {
            "inline_keyboard": inline_keyboard
        }
        
    res = requests.post(url, json=payload, timeout=10)
    res.raise_for_status()
