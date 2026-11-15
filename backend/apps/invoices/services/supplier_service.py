import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import httpx
from django.core.cache import cache
from apps.core.models import Organization
from apps.loyalty.services import IikoServerAuthService

logger = logging.getLogger(__name__)


class IikoSupplierService:
    def __init__(self, organization: Organization):
        self.org = organization

    def get_suppliers(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Возвращает список поставщиков из iiko Server. Кэшируется на 30 минут.
        """
        cache_key = f"iiko_suppliers_{self.org.id}"
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        suppliers = []
        if not self.org.iiko_server_url:
            return suppliers

        auth = IikoServerAuthService(self.org)
        token = auth.get_access_token()
        base_url = self.org.iiko_server_url.rstrip('/')
        url = f"{base_url}/resto/api/suppliers"

        try:
            with httpx.Client(timeout=30, verify=False) as client:
                resp = client.get(url, params={"key": token})
                if resp.status_code == 200:
                    # XML ответ
                    try:
                        root = ET.fromstring(resp.text)
                        for elem in root.findall('.//employee'):
                            sid = elem.findtext('id')
                            name = elem.findtext('name')
                            code = elem.findtext('code') or ""
                            inn = elem.findtext('taxpayerId') or elem.findtext('inn') or ""
                            deleted = elem.findtext('deleted') == 'true'
                            if not deleted and sid and name:
                                suppliers.append({
                                    "id": sid,
                                    "name": name,
                                    "code": code,
                                    "inn": inn
                                })
                    except ET.ParseError:
                        # Если вдруг вернулся JSON
                        try:
                            data = resp.json()
                            for item in (data if isinstance(data, list) else data.get('suppliers', [])):
                                suppliers.append({
                                    "id": str(item.get("id")),
                                    "name": item.get("name", ""),
                                    "code": item.get("code", ""),
                                    "inn": item.get("inn") or item.get("taxpayerId") or ""
                                })
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Error fetching suppliers for org {self.org.id}: {e}")

        cache.set(cache_key, suppliers, timeout=1800)
        return suppliers

    def match_supplier_by_name_or_inn(self, raw_name: str, inn: str = "") -> Optional[Dict[str, Any]]:
        """
        Поиск поставщика по точному совпадению ИНН или максимальной похожести названия.
        """
        suppliers = self.get_suppliers()
        if not suppliers:
            return None

        clean_inn = (inn or "").strip()
        if clean_inn:
            for s in suppliers:
                if s.get("inn") and s["inn"].strip() == clean_inn:
                    return s

        if not raw_name:
            return None

        from rapidfuzz import fuzz, process
        names = [s["name"] for s in suppliers]
        match = process.extractOne(raw_name, names, scorer=fuzz.token_sort_ratio)
        if match and match[1] >= 85:
            index = match[2]
            return suppliers[index]

        return None

    def create_supplier(self, name: str, inn: str = "", code: str = "", phone: str = "") -> Dict[str, Any]:
        """
        Создает нового поставщика в iiko Server.
        """
        if not self.org.iiko_server_url:
            raise ValueError("Адрес iiko Server не настроен")

        auth = IikoServerAuthService(self.org)
        token = auth.get_access_token()
        base_url = self.org.iiko_server_url.rstrip('/')
        url = f"{base_url}/resto/api/suppliers"

        # Формируем XML для создания контрагента/поставщика
        import uuid
        supplier_id = str(uuid.uuid4()).upper()
        xml_payload = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<employee>
    <id>{supplier_id}</id>
    <name>{name}</name>
    <code>{code or ''}</code>
    <taxpayerId>{inn or ''}</taxpayerId>
    <phone>{phone or ''}</phone>
    <supplier>true</supplier>
</employee>
"""
        headers = {"Content-Type": "application/xml; charset=utf-8"}
        with httpx.Client(timeout=30, verify=False) as client:
            resp = client.post(url, content=xml_payload.encode('utf-8'), params={"key": token}, headers=headers)
            if resp.status_code in (200, 201):
                # Сбрасываем кэш
                cache.delete(f"iiko_suppliers_{self.org.id}")
                return {
                    "id": supplier_id,
                    "name": name,
                    "inn": inn,
                    "code": code
                }
            else:
                logger.error(f"Failed to create supplier in iiko: {resp.status_code} {resp.text}")
                raise ValueError(f"Ошибка iiko при создании поставщика: {resp.text}")
