import logging
from datetime import datetime, date, timedelta
from django.db.models import Sum
from apps.core.models import Organization
from apps.analytics.models import FoodCostReport, ProductStockSnapshot, DailyOlapReport
from apps.analytics.services import IikoOlapService
from apps.inventory.services import IikoInventoryService
from apps.inventory.models import ProductPurchaseHistory

logger = logging.getLogger(__name__)

def sync_theoretical_food_cost(org: Organization, target_date: date):
    """
    Fetches daily theoretical sales and COGS from iiko OLAP report
    grouped by DishCategory, and updates FoodCostReport records.
    """
    logger.info(f"Syncing theoretical food cost for {org.name} on {target_date}")
    olap_service = IikoOlapService(org)
    
    group_by = ["DishCategory"]
    aggregates = ["DishSumInt", "ProductCostBase.ProductCost"]
    
    try:
        rows = olap_service.get_olap_report(target_date, target_date, group_by, aggregates)
    except Exception as e:
        logger.error(f"Failed to fetch theoretical OLAP food cost for org {org.id}: {e}")
        return
        
    if not rows:
        logger.warning(f"No theoretical OLAP food cost data returned for {target_date}")
        return

    total_revenue = 0.0
    total_cost = 0.0

    # Save category-level theoretical metrics
    for row in rows:
        category = row.get("DishCategory") or "Без категории"
        revenue = float(row.get("DishSumInt", 0.0))
        
        cost = row.get("ProductCostBase.ProductCost")
        if cost is None:
            cost = row.get("DishCost.ProductCost", 0.0)
        cost = float(cost)
        
        theoretical_fc_pct = (cost / revenue * 100) if revenue > 0 else 0.0
        
        FoodCostReport.objects.update_or_create(
            organization=org,
            date=target_date,
            category_name=category,
            defaults={
                "revenue": revenue,
                "theoretical_cost": cost,
                "theoretical_foodcost_percent": theoretical_fc_pct
            }
        )
        
        total_revenue += revenue
        total_cost += cost

    # Save overall restaurant-level theoretical metrics
    total_fc_pct = (total_cost / total_revenue * 100) if total_revenue > 0 else 0.0
    FoodCostReport.objects.update_or_create(
        organization=org,
        date=target_date,
        category_name="Все",
        defaults={
            "revenue": total_revenue,
            "theoretical_cost": total_cost,
            "theoretical_foodcost_percent": total_fc_pct
        }
    )
    logger.info(f"Completed theoretical food cost sync for {org.name} on {target_date}. Total Revenue: {total_revenue}, COGS: {total_cost}")


def take_stock_snapshot(org: Organization, target_date: date):
    """
    Fetches current stock levels from iiko and saves them to ProductStockSnapshot.
    Falls back to ProductPurchaseHistory to resolve product cost if not returned by iiko.
    """
    logger.info(f"Taking stock balance snapshot for {org.name} on {target_date}")
    inv_service = IikoInventoryService(org)
    
    try:
        balances = inv_service.fetch_stock_balances()
    except Exception as e:
        logger.error(f"Failed to fetch stock balances for org {org.id}: {e}")
        return
        
    if not balances:
        logger.warning(f"No stock balances returned for {org.name} on {target_date}")
        return

    count = 0
    for item in balances:
        prod_id = item.get("productId")
        prod_name = item.get("productName") or "Неизвестный товар"
        balance = float(item.get("balance", 0.0))
        
        # Check if iiko returns cost/price, otherwise resolve from purchase history
        cost = item.get("cost") or item.get("price")
        if cost is None:
            # Fallback: get the latest purchase price in the last 6 months
            latest_purchase = ProductPurchaseHistory.objects.filter(
                organization=org,
                product_id=prod_id,
                date__gte=target_date - timedelta(days=180)
            ).order_by('-date', '-created_at').first()
            cost = float(latest_purchase.price) if latest_purchase else 0.0
        else:
            cost = float(cost)
            
        ProductStockSnapshot.objects.update_or_create(
            organization=org,
            date=target_date,
            product_id=prod_id,
            defaults={
                "product_name": prod_name,
                "balance": balance,
                "cost": cost
            }
        )
        count += 1
        
    logger.info(f"Saved {count} stock snapshots for {org.name} on {target_date}")


def calculate_actual_food_cost(org: Organization, start_date: date, end_date: date):
    """
    Calculates actual food cost and variance over a bi-weekly (or any custom) period
    using formula: Actual COGS = Beginning Stock + Purchases - Ending Stock.
    Updates the FoodCostReport record on end_date with actual metrics.
    """
    logger.info(f"Calculating actual food cost for {org.name} from {start_date} to {end_date}")
    
    # 1. Beginning Stock Value
    beg_snapshots = ProductStockSnapshot.objects.filter(organization=org, date=start_date)
    beg_val = sum(float(s.balance * s.cost) for s in beg_snapshots)
    
    # 2. Ending Stock Value
    end_snapshots = ProductStockSnapshot.objects.filter(organization=org, date=end_date)
    end_val = sum(float(s.balance * s.cost) for s in end_snapshots)
    
    # If snapshots are missing, log warning
    if not beg_snapshots.exists() or not end_snapshots.exists():
        logger.warning(
            f"Missing stock snapshots for actual food cost calculation. "
            f"Start date snapshots: {beg_snapshots.count()}, End date snapshots: {end_snapshots.count()}"
        )
        return
        
    # 3. Purchases Value between start_date and end_date (inclusive)
    purchases = ProductPurchaseHistory.objects.filter(
        organization=org,
        date__gte=start_date,
        date__lte=end_date
    )
    purchases_val = sum(float(p.price * p.quantity) for p in purchases)
    
    # 4. Actual COGS
    actual_cogs = beg_val + purchases_val - end_val
    if actual_cogs < 0:
        logger.warning(f"Calculated negative Actual COGS: {actual_cogs}. Check inventory data.")
        actual_cogs = 0.0
        
    # 5. Total Revenue in the period
    reports = DailyOlapReport.objects.filter(
        organization=org,
        date__gte=start_date,
        date__lte=end_date
    )
    total_revenue = float(reports.aggregate(total_rev=Sum('revenue'))['total_rev'] or 0.0)
    
    actual_fc_pct = (actual_cogs / total_revenue * 100) if total_revenue > 0 else 0.0
    
    # 6. Total Theoretical COGS in the period
    theoretical_reports = FoodCostReport.objects.filter(
        organization=org,
        category_name="Все",
        date__gte=start_date,
        date__lte=end_date
    )
    total_theo_cogs = float(theoretical_reports.aggregate(total_theo=Sum('theoretical_cost'))['total_theo'] or 0.0)
    theoretical_fc_pct = (total_theo_cogs / total_revenue * 100) if total_revenue > 0 else 0.0
    
    # 7. Variance
    variance_cogs = actual_cogs - total_theo_cogs
    variance_pct = actual_fc_pct - theoretical_fc_pct
    
    # Save the aggregated actual food cost to the report on the end_date (inventory date)
    FoodCostReport.objects.update_or_create(
        organization=org,
        date=end_date,
        category_name="Все",
        defaults={
            "actual_cost": actual_cogs,
            "actual_foodcost_percent": actual_fc_pct,
            "variance_cost": variance_cogs,
            "variance_percent": variance_pct
        }
    )
    logger.info(
        f"Calculated actual food cost for {org.name} on {end_date}: "
        f"Beg Stock: {beg_val}, Purchases: {purchases_val}, End Stock: {end_val}, "
        f"Actual COGS: {actual_cogs}, Revenue: {total_revenue}, FC%: {actual_fc_pct}%, Variance: {variance_pct}%"
    )
