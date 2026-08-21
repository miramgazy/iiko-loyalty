import httpx
import logging
from datetime import datetime, date, timedelta
from django.conf import settings
from apps.core.models import Organization
from apps.loyalty.services import IikoAuthService, IikoServerAuthService
from apps.analytics.models import DailyOlapReport, HourlyOlapReport

logger = logging.getLogger(__name__)

class IikoOlapService:
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

    def get_olap_report(self, from_date: date, to_date: date, group_by_fields: list, aggregate_fields: list) -> list:
        if (to_date - from_date).days > 31:
            raise ValueError("Период запроса не должен превышать 31 день во избежание перегрузки сервера iiko")

        from datetime import timedelta
        from django.core.cache import cache
        
        # Detect if we should use classic Server API or Cloud API
        is_cloud = False
        if not self.org.iiko_server_url:
            base = self.org.iiko_api_base_url.rstrip('/')
            if 'api-ru.iiko.services' in base or '/api/1' in base:
                is_cloud = True
                
        parsed_rows = []
        
        # Split into sequential chunks of max 7 days (6 days offset)
        current_from = from_date
        while current_from <= to_date:
            current_to = min(current_from + timedelta(days=6), to_date)
            
            payload = {
              "reportType": "SALES",
              "groupByRowFields": group_by_fields,
              "groupByColFields": [],
              "aggregateFields": aggregate_fields,
              "filters": {
                "OpenDate.Typed": {
                  "filterType": "DateRange",
                  "periodType": "CUSTOM",
                  "from": current_from.strftime("%Y-%m-%d"),
                  "to": (current_to + timedelta(days=1)).strftime("%Y-%m-%d")
                }
              }
            }

            if is_cloud:
                if self.org.iiko_organization_id:
                    payload["organizationIds"] = [str(self.org.iiko_organization_id)]
                url = self._get_api_url("/reports/olap")
                with httpx.Client(timeout=45) as client:
                    response = client.post(url, json=payload, headers=self._get_headers())
                    response.raise_for_status()
                    res_data = response.json()
            else:
                # Classic Server API
                server_auth = IikoServerAuthService(self.org)
                token = server_auth.get_access_token()
                
                # Use iiko_server_url if set, otherwise fallback to base url
                base = (self.org.iiko_server_url or self.org.iiko_api_base_url).rstrip('/')
                
                # Ensure correct v2 endpoint prefix
                v2_base = base
                for suffix in ['/resto/api/v2', '/resto/api/v1', '/resto/api', '/resto', '/api/v2', '/api/v1', '/api/1', '/api']:
                    if v2_base.endswith(suffix):
                        v2_base = v2_base[:-len(suffix)]
                        break
                v2_base = f"{v2_base.rstrip('/')}/resto/api/v2"
                
                url = f"{v2_base}/reports/olap"
                params = {
                    "key": token
                }
                
                with httpx.Client(timeout=45, verify=False) as client:
                    response = client.post(url, json=payload, params=params)
                    if response.status_code == 401:
                        cache.delete(server_auth.cache_key)
                        token = server_auth.get_access_token()
                        params["key"] = token
                        response = client.post(url, json=payload, params=params)
                    response.raise_for_status()
                    res_data = response.json()
                
            # Parse the response format
            columns = [col["name"] for col in res_data.get("columns", [])] if isinstance(res_data, dict) else []
            if isinstance(res_data, dict):
                data_rows = res_data.get("data", [])
            elif isinstance(res_data, list):
                data_rows = res_data
            else:
                data_rows = []
            
            for row in data_rows:
                if not isinstance(row, dict):
                    continue
                if "values" in row and columns:
                    values = row.get("values", [])
                    parsed_row = dict(zip(columns, values))
                else:
                    parsed_row = row
                parsed_rows.append(parsed_row)
                
            current_from = current_to + timedelta(days=1)
            
        return parsed_rows

    def get_olap_by_preset(self, preset_id: str, from_date: date, to_date: date) -> list:
        """
        Loads OLAP report data by preset UUID using either iiko Cloud or iiko Server v2 API.
        """
        import json
        from django.core.cache import cache
        from datetime import timedelta
        
        # Cache key based on org, preset, and dates
        cache_key = f"iiko_olap_preset_{self.org.id}_{preset_id}_{from_date}_{to_date}"
        try:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"Returning cached OLAP preset data for {preset_id}")
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Redis cache lookup failed: {e}")

        # Enforce date range limit of maximum 31 days total
        if (to_date - from_date).days > 31:
            raise ValueError("Период запроса не должен превышать 31 день во избежание перегрузки сервера iiko")

        # Detect if we should use classic Server API or Cloud API
        is_cloud = False
        if not self.org.iiko_server_url:
            base = self.org.iiko_api_base_url.rstrip('/')
            if 'api-ru.iiko.services' in base or '/api/1' in base:
                is_cloud = True
        
        parsed_rows = []
        
        # Split into sequential chunks of max 7 days (6 days offset)
        current_from = from_date
        while current_from <= to_date:
            current_to = min(current_from + timedelta(days=6), to_date)
            
            if is_cloud:
                base = self.org.iiko_api_base_url.rstrip('/')
                url = f"{base}/reports/olap/by_preset"
                payload = {
                    "presetId": str(preset_id),
                    "organizationId": str(self.org.iiko_organization_id),
                    "dateFrom": current_from.strftime("%Y-%m-%d"),
                    "dateTo": (current_to + timedelta(days=1)).strftime("%Y-%m-%d")
                }
                with httpx.Client(timeout=45) as client:
                    response = client.post(url, json=payload, headers=self._get_headers())
                    response.raise_for_status()
                    res_data = response.json()
            else:
                # Classic Server API
                server_auth = IikoServerAuthService(self.org)
                token = server_auth.get_access_token()
                
                # Use iiko_server_url if set, otherwise fallback to base url
                base = (self.org.iiko_server_url or self.org.iiko_api_base_url).rstrip('/')
                
                # Ensure correct v2 endpoint prefix
                v2_base = base
                for suffix in ['/resto/api/v2', '/resto/api/v1', '/resto/api', '/resto', '/api/v2', '/api/v1', '/api/1', '/api']:
                    if v2_base.endswith(suffix):
                        v2_base = v2_base[:-len(suffix)]
                        break
                v2_base = f"{v2_base.rstrip('/')}/resto/api/v2"
                    
                url = f"{v2_base}/reports/olap/byPresetId/{preset_id}"
                params = {
                    "dateFrom": current_from.strftime("%Y-%m-%d"),
                    "dateTo": (current_to + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "key": token
                }
                
                with httpx.Client(timeout=45, verify=False) as client:
                    response = client.get(url, params=params)
                    if response.status_code == 401:
                        cache.delete(server_auth.cache_key)
                        token = server_auth.get_access_token()
                        params["key"] = token
                        response = client.get(url, params=params)
                    response.raise_for_status()
                    res_data = response.json()
                    
            # Parse standard iiko OLAP columns and values for this chunk
            columns = [col["name"] for col in res_data.get("columns", [])] if isinstance(res_data, dict) else []
            if isinstance(res_data, dict):
                data_rows = res_data.get("data", [])
            elif isinstance(res_data, list):
                data_rows = res_data
            else:
                data_rows = []
            
            for row in data_rows:
                if not isinstance(row, dict):
                    continue
                if "values" in row and columns:
                    values = row.get("values", [])
                    parsed_row = dict(zip(columns, values))
                else:
                    parsed_row = row
                parsed_rows.append(parsed_row)
                
            current_from = current_to + timedelta(days=1)
            
        # Cache results in Redis for 15 minutes (900 seconds)
        try:
            cache.set(cache_key, json.dumps(parsed_rows), timeout=900)
        except Exception as e:
            logger.error(f"Failed to write OLAP preset data to Redis: {e}")
            
        return parsed_rows


def sync_daily_olap_for_date(org: Organization, target_date: date):
    logger.info(f"Syncing daily OLAP for org {org.name} on {target_date}")
    service = IikoOlapService(org)
    
    from apps.analytics.models import IikoOlapPreset
    preset = IikoOlapPreset.objects.filter(organization=org, report_type_key='daily_kpi').first()
    
    try:
        # Check if preset exists and has a non-default UUID
        if preset and preset.preset_id and str(preset.preset_id) != "00000000-0000-0000-0000-000000000000":
            rows = service.get_olap_by_preset(preset.preset_id, target_date, target_date)
        else:
            group_by = ["OpenDate.Typed"]
            aggregates = ["DishSumInt", "ProductCostBase.ProductCost", "DishDiscountSumInt", "UniqOrderId", "GuestNum"]
            rows = service.get_olap_report(target_date, target_date, group_by, aggregates)
            
        if not rows:
            logger.warning(f"No OLAP data returned for {target_date}")
            return
        
        row = rows[0]
        # Support both standard key formats (UniqOrderId vs ChecksCount and ProductCostBase.ProductCost vs DishCost.ProductCost)
        cost_val = row.get("ProductCostBase.ProductCost")
        if cost_val is None:
            cost_val = row.get("DishCost.ProductCost", 0.0)
            
        checks_val = row.get("UniqOrderId")
        if checks_val is None:
            checks_val = row.get("ChecksCount", 0)
            
        DailyOlapReport.objects.update_or_create(
            organization=org,
            date=target_date,
            defaults={
                "revenue": row.get("DishSumInt", 0.0),
                "cost": cost_val,
                "discounts": row.get("DishDiscountSumInt", 0.0),
                "checks_count": int(checks_val),
                "guests_count": int(row.get("GuestNum", 0)),
            }
        )
    except Exception as e:
        logger.error(f"Error syncing daily OLAP: {e}", exc_info=True)


def sync_hourly_olap_for_date(org: Organization, target_date: date):
    logger.info(f"Syncing hourly OLAP for org {org.name} on {target_date}")
    service = IikoOlapService(org)
    
    from apps.analytics.models import IikoOlapPreset
    preset = IikoOlapPreset.objects.filter(organization=org, report_type_key='hourly_sales').first()
    
    try:
        # Check if preset exists and has a non-default UUID
        if preset and preset.preset_id and str(preset.preset_id) != "00000000-0000-0000-0000-000000000000":
            rows = service.get_olap_by_preset(preset.preset_id, target_date, target_date)
        else:
            group_by = ["OpenDate.Typed", "HourOpen", "DishId", "DishName"]
            aggregates = ["DishAmountInt", "DishSumInt"]
            rows = service.get_olap_report(target_date, target_date, group_by, aggregates)
        
        # Clear existing hourly records for this date
        HourlyOlapReport.objects.filter(organization=org, date=target_date).delete()
        
        objs = []
        for row in rows:
            hour_val = row.get("HourOpen")
            if hour_val is None:
                hour_val = row.get("Hour", 0)
            hour = int(hour_val)
            
            product_id = row.get("DishId")
            product_name = row.get("DishName", "")
            
            qty_val = row.get("DishAmountInt")
            if qty_val is None:
                qty_val = row.get("DishQty", 0.0)
            quantity = float(qty_val)
            
            revenue = float(row.get("DishSumInt", 0.0))
            
            if not product_id:
                continue
                
            objs.append(HourlyOlapReport(
                organization=org,
                date=target_date,
                hour=hour,
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                revenue=revenue
            ))
            
        HourlyOlapReport.objects.bulk_create(objs)
        logger.info(f"Successfully synced {len(objs)} hourly records")
    except Exception as e:
        logger.error(f"Error syncing hourly OLAP: {e}", exc_info=True)


def get_dashboard_kpis(org, target_date: date):
    # Fetch data for target_date
    current_report = DailyOlapReport.objects.filter(organization=org, date=target_date).first()
    
    # Same day last week
    last_week_date = target_date - timedelta(days=7)
    last_week_report = DailyOlapReport.objects.filter(organization=org, date=last_week_date).first()
    
    # Same day last month
    last_month_date = target_date - timedelta(days=30)
    last_month_report = DailyOlapReport.objects.filter(organization=org, date=last_month_date).first()
    
    def format_kpi(report):
        if not report:
            return {
                "revenue": 0.0,
                "cost": 0.0,
                "profit": 0.0,
                "avg_check": 0.0,
                "checks_count": 0,
                "guests_count": 0,
                "foodcost_percent": 0.0
            }
        revenue = float(report.revenue)
        cost = float(report.cost)
        profit = revenue - cost
        checks = report.checks_count
        guests = report.guests_count
        
        avg_check = revenue / checks if checks > 0 else 0.0
        foodcost_percent = (cost / revenue * 100) if revenue > 0 else 0.0
        
        return {
            "revenue": revenue,
            "cost": cost,
            "profit": profit,
            "avg_check": avg_check,
            "checks_count": checks,
            "guests_count": guests,
            "foodcost_percent": foodcost_percent
        }
        
    current_data = format_kpi(current_report)
    last_week_data = format_kpi(last_week_report)
    last_month_data = format_kpi(last_month_report)
    
    def pct_change(curr, prev):
        if prev == 0.0:
            return 100.0 if curr > 0.0 else 0.0
        return ((curr - prev) / prev) * 100.0
        
    comparison = {}
    for key in ["revenue", "profit", "avg_check", "checks_count", "guests_count"]:
        comparison[key] = {
            "value": current_data[key],
            "last_week_diff_pct": pct_change(current_data[key], last_week_data[key]),
            "last_month_diff_pct": pct_change(current_data[key], last_month_data[key]),
        }
        
    comparison["foodcost_percent"] = {
        "value": current_data["foodcost_percent"],
        "last_week_diff": current_data["foodcost_percent"] - last_week_data["foodcost_percent"],
        "last_month_diff": current_data["foodcost_percent"] - last_month_data["foodcost_percent"],
    }
    
    return comparison

