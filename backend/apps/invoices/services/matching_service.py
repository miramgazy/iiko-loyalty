import re
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
import xml.etree.ElementTree as ET
import httpx
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
from rapidfuzz import fuzz, process

from apps.core.models import Organization
from apps.loyalty.services import IikoServerAuthService, IikoAuthService
from apps.invoices.models import SupplierProductAlias, InvoiceItem, IikoProductEmbedding
from apps.invoices.services.calculation_service import PackagingCalculationService
from apps.invoices.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


def normalize_product_name(s: str) -> str:
    if not s:
        return ""
    s = s.lower().replace('ё', 'е')
    # Заменяем знаки препинания на пробелы
    s = re.sub(r'["\'«»“”()\[\],.:;!/?\\_+\-*#%№@]', ' ', s)
    # Удаляем распространенные стоп-слова, юр. формы и тару
    stop_words = {
        'ооо', 'зао', 'оао', 'пао', 'тоо', 'ип', 'чуп', 'тм',
        'кг', 'гр', 'г', 'л', 'мл', 'шт', 'уп', 'кор', 'бан',
        'арт', 'артикул', 'код', 'сорт', 'кат', 'срт', 'категория',
        'блок', 'ящик', 'пакет', 'бутылка', 'бут', 'упак', 'пачка', 'пач',
        'нетто', 'брутто', 'вес', 'весовой', 'охл', 'зам', 'с/м'
    }
    tokens = [w for w in s.split() if w not in stop_words and not (w.isdigit() and len(w) >= 4)]
    return ' '.join(tokens)


def score_catalog_item(clean_name: str, raw_name: str, norm_clean: str, norm_raw: str, prod: Dict[str, Any]) -> float:
    """
    Вычисляет оценку схожести (0.0..1.0) между товаром из накладной и позицией каталога iiko.
    Приоритет отдается очищенному смысловому наименованию clean_name.
    """
    prod_name = prod.get('name', '')
    if not prod_name:
        return 0.0

    norm_prod = normalize_product_name(prod_name)

    # 1. Точное совпадение после нормализации
    if norm_prod and (norm_prod == norm_clean or norm_prod == norm_raw):
        return 1.0

    # 2. Полное вхождение подстроки (например "сыр моцарелла" полностью входит в "сыр моцарелла 45%")
    if norm_prod and len(norm_prod) >= 4:
        if (norm_clean and norm_prod in norm_clean) or (norm_raw and norm_prod in norm_raw):
            return 0.95
        if norm_clean and norm_clean in norm_prod:
            return 0.92

    # 3. Метрики на clean_name (primary)
    score_clean = 0.0
    if clean_name:
        w_clean = fuzz.WRatio(clean_name, prod_name)
        set_clean = fuzz.token_set_ratio(clean_name, prod_name)
        score_clean = max(w_clean, set_clean)

    # 4. Метрики на raw_name (secondary, с небольшой скидкой на шум)
    score_raw = 0.0
    if raw_name:
        w_raw = fuzz.WRatio(raw_name, prod_name)
        set_raw = fuzz.token_set_ratio(raw_name, prod_name)
        score_raw = max(w_raw, set_raw) * 0.90

    # 5. Проверка совпадения артикула iiko в тексте накладной
    prod_code = str(prod.get('code') or '').strip()
    if prod_code and len(prod_code) >= 3 and prod_code in raw_name:
        return 0.98

    best = max(score_clean, score_raw)
    return round(best / 100.0, 3)


class InvoiceMatchingService:
    def __init__(self, organization: Organization):
        self.org = organization

    def get_cached_products(self) -> List[Dict[str, Any]]:
        """
        Возвращает список товаров организации из iiko (кэшируется на 1 час).
        Каждый элемент: {'id': 'uuid', 'name': 'Название', 'code': '123', 'unit': 'кг', 'containers': [...]}
        """
        cache_key = f"iiko_products_catalog_{self.org.id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        products = self._fetch_products_from_iiko()
        if products:
            cache.set(cache_key, products, timeout=3600)
        return products

    def _fetch_assembly_charts_strategies(self, base_url: str, token: str) -> Dict[str, str]:
        """
        Запрашивает актуальные технологические карты (/resto/api/v2/assemblyCharts/getAll)
        и возвращает словарь {assembledProductId: productWriteoffStrategy}.
        - 'ASSEMBLE': списание по ингредиентам (кухонные блюда, соусы, полуфабрикаты). Исключаем!
        - 'DIRECT': списание готовым блюдом (самостоятельные штучные единицы на складе). Оставляем!
        """
        strategies = {}
        try:
            today_str = timezone.now().date().strftime("%Y-%m-%d")
            url = f"{base_url}/resto/api/v2/assemblyCharts/getAll"
            with httpx.Client(timeout=30, verify=False) as client:
                resp = client.get(url, params={"key": token, "dateFrom": today_str, "dateTo": today_str})
                if resp.status_code == 200:
                    data = resp.json()
                    charts = data.get("assemblyCharts", []) if isinstance(data, dict) else data
                    for c in charts:
                        pid = c.get("assembledProductId")
                        strategy = c.get("productWriteoffStrategy")
                        if pid and strategy:
                            strategies[str(pid).lower()] = strategy
        except Exception as e:
            logger.warning(f"Failed to fetch assembly charts for org {self.org.id}: {e}")
        return strategies

    def _fetch_products_from_iiko(self) -> List[Dict[str, Any]]:
        products = []

        # 1. Попытка получить номенклатуру из iiko Server (RMS REST API)
        if self.org.iiko_server_url:
            try:
                auth_service = IikoServerAuthService(self.org)
                token = auth_service.get_access_token()
                base_url = self.org.iiko_server_url.rstrip('/')

                # Получаем стратегии списания из активных ТТК
                strategies = self._fetch_assembly_charts_strategies(base_url, token)

                # Попытка v2 JSON
                v2_url = f"{base_url}/resto/api/v2/entities/products/list"
                with httpx.Client(timeout=30, verify=False) as client:
                    resp = client.get(v2_url, params={"key": token})
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_items = data if isinstance(data, list) else data.get("products", [])
                        for item in raw_items:
                            if item.get("deleted"):
                                continue

                            ptype = (item.get("type") or "GOODS").upper()
                            # Исключаем услуги, модификаторы, тарифы
                            if ptype in ("SERVICE", "MODIFIER", "RATE"):
                                continue

                            pid = str(item.get("id")).lower()
                            strategy = strategies.get(pid)

                            # Для блюд и заготовок:
                            # Если списание по ингредиентам (ASSEMBLE) -> исключаем!
                            # Если списание готовым блюдом (DIRECT) -> оставляем!
                            if ptype in ("DISH", "PREPARED"):
                                if strategy == "ASSEMBLE":
                                    continue
                                if strategy != "DIRECT" and ptype == "DISH":
                                    continue

                            products.append({
                                "id": str(item.get("id")),
                                "name": item.get("name", ""),
                                "code": item.get("code") or item.get("article") or "",
                                "unit": item.get("mainUnit") or item.get("unit") or "кг",
                                "containers": item.get("containers", []),
                                "type": ptype
                            })
                        if products:
                            return products

                # Fallback на v1 XML /resto/api/products
                v1_url = f"{base_url}/resto/api/products"
                with httpx.Client(timeout=30, verify=False) as client:
                    resp = client.get(v1_url, params={"key": token})
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.text)
                        for prod_elem in root.findall('.//productDto'):
                            pid = prod_elem.findtext('id')
                            name = prod_elem.findtext('name')
                            code = prod_elem.findtext('num') or prod_elem.findtext('code') or ""
                            main_unit = prod_elem.findtext('mainUnit') or "кг"
                            deleted = prod_elem.findtext('deleted') == 'true'
                            ptype = (prod_elem.findtext('productType') or prod_elem.findtext('type') or 'GOODS').upper()

                            if deleted or not pid or not name:
                                continue

                            if ptype in ("SERVICE", "MODIFIER", "RATE"):
                                continue

                            pid_lower = str(pid).lower()
                            strategy = strategies.get(pid_lower)
                            if ptype in ("DISH", "PREPARED"):
                                if strategy == "ASSEMBLE":
                                    continue
                                if strategy != "DIRECT" and ptype == "DISH":
                                    continue

                            products.append({
                                "id": pid,
                                "name": name,
                                "code": code,
                                "unit": main_unit,
                                "containers": [],
                                "type": ptype
                            })
                        if products:
                            return products
            except Exception as e:
                logger.warning(f"Failed to fetch products from iiko Server for org {self.org.id}: {e}")

        # 2. Fallback на iiko Cloud Transport API (если доступен)
        if self.org.iiko_api_login and self.org.iiko_organization_id:
            try:
                cloud_auth = IikoAuthService(self.org)
                token = cloud_auth.get_access_token()
                base_cloud = self.org.iiko_api_base_url.rstrip('/')
                if '/api/v2' in base_cloud:
                    base_cloud = base_cloud.replace('/api/v2', '/api/1')
                url = f"{base_cloud}/nomenclature"
                payload = {"organizationId": str(self.org.iiko_organization_id)}
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                with httpx.Client(timeout=30) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        for p in data.get("products", []):
                            if p.get("isDeleted"):
                                continue
                            ptype = (p.get("type") or "GOODS").upper()
                            if ptype in ("SERVICE", "MODIFIER", "RATE", "DISH"):
                                continue
                            products.append({
                                "id": str(p.get("id")),
                                "name": p.get("name", ""),
                                "code": p.get("code") or "",
                                "unit": p.get("unit") or "кг",
                                "containers": [],
                                "type": ptype
                            })
            except Exception as e:
                logger.error(f"Failed to fetch nomenclature from iiko Cloud for org {self.org.id}: {e}")

        return products

    def _find_vector_candidates(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Выполняет семантический векторный поиск в pgvector (IikoProductEmbedding)
        по тексту (clean_name или raw_name).
        """
        if not query_text:
            return []

        emb_service = EmbeddingService(self.org)
        if not emb_service.is_configured():
            return []

        try:
            has_embeddings = IikoProductEmbedding.objects.filter(
                organization=self.org,
                embedding__isnull=False
            ).exists()
            if not has_embeddings:
                return []

            query_vec = emb_service.get_embedding(query_text)
            if not query_vec:
                return []

            vector_candidates = []
            if connection.vendor == 'postgresql':
                from pgvector.django import CosineDistance
                qs = (
                    IikoProductEmbedding.objects.filter(
                        organization=self.org,
                        embedding__isnull=False
                    )
                    .annotate(distance=CosineDistance('embedding', query_vec))
                    .order_by('distance')[:10]
                )
                for item in qs:
                    dist = float(item.distance) if item.distance is not None else 1.0
                    sim = round(max(0.0, 1.0 - dist), 3)
                    if sim >= 0.40:
                        vector_candidates.append({
                            'id': str(item.iiko_product_id),
                            'name': item.name,
                            'code': item.code or '',
                            'unit': item.unit or 'кг',
                            'score': sim,
                            'source': 'vector'
                        })
            else:
                # Python / NumPy fallback для SQLite и модульных тестов
                import numpy as np
                emb_items = list(
                    IikoProductEmbedding.objects.filter(
                        organization=self.org,
                        embedding__isnull=False
                    )[:2000]
                )
                if emb_items:
                    q_arr = np.array(query_vec, dtype=np.float32)
                    q_norm = np.linalg.norm(q_arr)
                    if q_norm > 0:
                        q_arr = q_arr / q_norm
                        for item in emb_items:
                            v_arr = np.array(item.embedding, dtype=np.float32)
                            v_norm = np.linalg.norm(v_arr)
                            if v_norm > 0:
                                sim = float(np.dot(q_arr, v_arr / v_norm))
                                if sim >= 0.40:
                                    vector_candidates.append({
                                        'id': str(item.iiko_product_id),
                                        'name': item.name,
                                        'code': item.code or '',
                                        'unit': item.unit or 'кг',
                                        'score': round(sim, 3),
                                        'source': 'vector'
                                    })
                        vector_candidates.sort(key=lambda x: x['score'], reverse=True)
                        vector_candidates = vector_candidates[:10]

            return vector_candidates
        except Exception as e:
            logger.warning(f"Vector search failed for org {self.org.id}: {e}")
            return []

    def match_item(
        self,
        raw_name: str,
        clean_name: str = "",
        supplier_id: Optional[str] = None,
        raw_amount: float = 0.0,
        raw_price: float = 0.0,
        raw_sum: float = 0.0,
        packaging_hint: str = ""
    ) -> Dict[str, Any]:
        """
        Сопоставляет строку документа со справочником iiko.
        Использует приоритет очищенного имени (clean_name), базу знаний и взвешенный алгоритм RapidFuzz.
        Возвращает:
        - match_status: 'green' | 'yellow' | 'red'
        - match_source: 'knowledge_base' | 'fuzzy' | 'manual'
        - confidence: float 0..1
        - product_id, product_name, product_code
        - packaging_coefficient
        - container_id, container_name
        - candidates: список топ-5 похожих вариантов
        """
        raw_name = (raw_name or "").strip()
        clean_name = (clean_name or "").strip()

        norm_raw = normalize_product_name(raw_name)
        norm_clean = normalize_product_name(clean_name) if clean_name else norm_raw

        # 1-й Уровень: База знаний (Exact Match по алиасам для поставщика)
        alias_query = SupplierProductAlias.objects.filter(organization=self.org)
        if supplier_id:
            alias_query = alias_query.filter(supplier_id=supplier_id)

        alias = (
            alias_query.filter(normalized_raw_name=norm_raw).first() or
            (alias_query.filter(normalized_raw_name=norm_clean).first() if norm_clean else None)
        )

        if alias:
            calc = PackagingCalculationService.calculate_item_values(
                raw_amount, raw_price, raw_sum, alias.default_packaging_coefficient
            )
            return {
                'match_status': InvoiceItem.MATCH_STATUS_GREEN,
                'match_source': 'knowledge_base',
                'confidence': 1.0,
                'product_id': str(alias.iiko_product_id),
                'product_name': alias.iiko_product_name,
                'product_code': '',
                'packaging_coefficient': float(alias.default_packaging_coefficient),
                'container_id': str(alias.default_container_id) if alias.default_container_id else None,
                'container_name': alias.default_container_name,
                'candidates': [],
                **calc
            }

        # Определение фасовки из текста
        packaging_coeff = Decimal('1.000')
        container_id = None
        container_name = ""

        full_text = f"{raw_name} {clean_name} {packaging_hint}".lower()
        weight_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(кг|г|гр|л|мл)\b', full_text)
        if weight_match:
            num_val = float(weight_match.group(1).replace(',', '.'))
            unit_val = weight_match.group(2)
            if unit_val in ('г', 'гр', 'мл'):
                packaging_coeff = Decimal(str(round(num_val / 1000.0, 3)))
            elif unit_val in ('кг', 'л'):
                packaging_coeff = Decimal(str(round(num_val, 3)))

        calc = PackagingCalculationService.calculate_item_values(
            raw_amount, raw_price, raw_sum, packaging_coeff
        )

        # 2-й Уровень: Умный поиск по каталогу iiko (RapidFuzz WRatio + token_set_ratio)
        catalog = self.get_cached_products() or []

        scored_candidates = []
        for prod in catalog:
            score = score_catalog_item(
                clean_name=clean_name,
                raw_name=raw_name,
                norm_clean=norm_clean,
                norm_raw=norm_raw,
                prod=prod
            )
            if score >= 0.35:
                scored_candidates.append({
                    'id': str(prod['id']),
                    'name': prod['name'],
                    'code': prod.get('code') or '',
                    'unit': prod.get('unit') or 'кг',
                    'score': score,
                    'source': 'fuzzy'
                })

        # 3-й Уровень: Семантический векторный поиск в pgvector
        query_text = clean_name if clean_name else raw_name
        vector_candidates = self._find_vector_candidates(query_text)

        # Объединяем результаты RapidFuzz и Vector search
        candidates_by_id = {}
        for c in scored_candidates:
            candidates_by_id[c['id']] = c

        for vc in vector_candidates:
            pid = vc['id']
            if pid in candidates_by_id:
                existing = candidates_by_id[pid]
                fuzz_sc = existing['score']
                vec_sc = vc['score']
                # Синергия: если и вектор, и fuzzy находят товар, оценка усиливается
                combined = max(fuzz_sc, vec_sc, round(0.5 * fuzz_sc + 0.5 * vec_sc + 0.05, 3))
                existing['score'] = min(combined, 1.0)
                existing['source'] = 'vector+fuzzy'
            else:
                candidates_by_id[pid] = vc

        combined_candidates = list(candidates_by_id.values())
        combined_candidates.sort(key=lambda x: x['score'], reverse=True)
        candidates = combined_candidates[:5]

        best_candidate = candidates[0] if candidates else None
        best_score = best_candidate['score'] if best_candidate else 0.0
        best_source = best_candidate.get('source', 'fuzzy') if best_candidate else 'fuzzy'

        # Градация уверенности:
        # Score >= 0.85 -> ЗЕЛЕНЫЙ (Точное / уверенное совпадение)
        # 0.55 <= Score < 0.85 -> ЖЕЛТЫЙ (Вероятный вариант, предлагаем подтвердить или выбрать из кандидатов)
        # Score < 0.55 -> КРАСНЫЙ (Не найдено, но кандидаты доступны для выбора в 1 клик)
        if best_score >= 0.85 and best_candidate:
            return {
                'match_status': InvoiceItem.MATCH_STATUS_GREEN,
                'match_source': best_source,
                'confidence': best_score,
                'product_id': best_candidate['id'],
                'product_name': best_candidate['name'],
                'product_code': best_candidate['code'],
                'packaging_coefficient': float(packaging_coeff),
                'container_id': container_id,
                'container_name': container_name,
                'candidates': candidates,
                **calc
            }
        elif best_score >= 0.55 and best_candidate:
            return {
                'match_status': InvoiceItem.MATCH_STATUS_YELLOW,
                'match_source': best_source,
                'confidence': best_score,
                'product_id': best_candidate['id'],
                'product_name': best_candidate['name'],
                'product_code': best_candidate['code'],
                'packaging_coefficient': float(packaging_coeff),
                'container_id': container_id,
                'container_name': container_name,
                'candidates': candidates,
                **calc
            }
        else:
            return {
                'match_status': InvoiceItem.MATCH_STATUS_RED,
                'match_source': 'manual',
                'confidence': best_score,
                'product_id': None,
                'product_name': '',
                'product_code': '',
                'packaging_coefficient': float(packaging_coeff),
                'container_id': container_id,
                'container_name': container_name,
                'candidates': candidates,
                **calc
            }
