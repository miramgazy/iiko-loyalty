import httpx
import json
import logging
import re
from datetime import datetime, date
from django.conf import settings
from django.db import connection
from apps.core.models import Organization
import sqlglot
from sqlglot import exp

logger = logging.getLogger(__name__)

ALLOWED_VIEWS = {"v_ai_daily_sales", "v_ai_payment_types", "v_ai_stop_list", "v_ai_product_purchases"}

def rewrite_and_validate_sql(query_str: str, org_id: int) -> str:
    try:
        # Parse all statements
        expressions = sqlglot.parse(query_str, read="postgres")
    except Exception as e:
        raise ValueError(f"Ошибка парсинга SQL: {e}")
        
    expressions = [exp for exp in expressions if exp]
    if len(expressions) != 1:
        raise ValueError("Ошибка безопасности: Допускается только один SQL-запрос.")
        
    expression = expressions[0]
    
    if not isinstance(expression, exp.Select):
        raise ValueError("Ошибка безопасности: Разрешены только SELECT-запросы.")
        
    forbidden_types = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter)
    for node in expression.find_all(forbidden_types):
        raise ValueError("Ошибка безопасности: Разрешены только SELECT-запросы.")

    tables = list(expression.find_all(exp.Table))
    if not tables:
        raise ValueError("Запрос должен содержать выборку из разрешенных таблиц/представлений.")
        
    for t in tables:
        tbl_name = t.name.lower()
        if tbl_name not in ALLOWED_VIEWS:
            raise ValueError(f"Доступ к таблице '{tbl_name}' запрещен. Разрешены только: {', '.join(ALLOWED_VIEWS)}")

    # Rewrite Table references to enforce organization filter
    def transform(node):
        if isinstance(node, exp.Table):
            view_name = node.name.lower()
            wrapped = sqlglot.parse_one(
                f"(SELECT * FROM {view_name} WHERE organization_id = {org_id})",
                read="postgres"
            )
            if node.alias:
                wrapped = wrapped.as_(node.alias)
            else:
                wrapped = wrapped.as_(view_name)
            return wrapped
        return node

    rewritten_expression = expression.transform(transform)
    
    # Enforce limit of 50
    if not rewritten_expression.args.get("limit"):
        rewritten_expression = rewritten_expression.limit(50)
        
    # Compile to SQLite or Postgres depending on Django database backend
    dialect = "sqlite" if connection.vendor == "sqlite" else "postgres"
    return rewritten_expression.sql(dialect=dialect)

def parse_agent_response(text: str) -> dict:
    text = text.strip()
    
    # Try parsing the whole text as JSON
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "text" in data:
            return {
                "response": data["text"],
                "chart": data.get("chart")
            }
    except Exception:
        pass

    # Try extracting JSON from markdown code block
    json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_block_match:
        try:
            data = json.loads(json_block_match.group(1))
            if isinstance(data, dict) and "text" in data:
                return {
                    "response": data["text"],
                    "chart": data.get("chart")
                }
        except Exception:
            pass
            
    # Try searching for any outer curly braces
    brace_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if brace_match:
        try:
            data = json.loads(brace_match.group(1))
            if isinstance(data, dict) and "text" in data:
                return {
                    "response": data["text"],
                    "chart": data.get("chart")
                }
        except Exception:
            pass

    # Fallback to plain text
    return {
        "response": text,
        "chart": None
    }

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_kpi_dashboard",
            "description": "Получить дашборд ключевых KPI ресторана за указанную дату (выручка, себестоимость, прибыль, фудкост, средний чек, количество гостей/чеков).",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "Дата в формате YYYY-MM-DD (например, 2026-08-19). Если не указана, используется текущая дата."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_drift",
            "description": "Получить анализ динамики цен сырья (Price Drift) - Топ подорожавших/подешевевших товаров за последнее время и финансовый урон.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stop_lists",
            "description": "Получить информацию об упущенной выручке и марже от нахождения блюд в стоп-листах.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_reports",
            "description": "Получить список всех настроенных отчетов организации (включая системные и кастомные) с их описанием и ID.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_report_data",
            "description": "Получить сырые данные OLAP-отчета по его preset_id за указанный период дат (date_from, date_to) для анализа.",
            "parameters": {
                "type": "object",
                "properties": {
                    "preset_id": {
                        "type": "string",
                        "description": "UUID пресета отчета из iiko RMS."
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Начальная дата периода в формате YYYY-MM-DD (например, 2026-08-18)."
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Конечная дата периода в формате YYYY-MM-DD (например, 2026-08-19)."
                    }
                },
                "required": ["preset_id", "date_from", "date_to"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "Получить список доступных представлений (SQL Views) в базе данных проекта (для прямого SQL-анализа).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_schema",
            "description": "Получить структуру и имена колонок для конкретного представления.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Имя представления (например, 'v_ai_daily_sales')."
                    }
                },
                "required": ["table_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": "Выполнить безопасный SQL-запрос на чтение (SELECT) к разрешенным представлениям и получить результаты. Лимит вывода - 50 строк.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL-запрос (например, 'SELECT * FROM v_ai_daily_sales WHERE date > \'2026-08-15\'')."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def execute_tool(org: Organization, name: str, arguments: dict, user=None) -> dict:
    from apps.analytics.services import get_dashboard_kpis
    from apps.inventory.services import calculate_price_drift
    from apps.inventory.models import StopListHistory
    from apps.inventory.serializers import StopListHistorySerializer
    
    logger.info(f"Executing tool {name} with arguments {arguments} for org {org.name}")
    try:
        if name == "get_kpi_dashboard":
            date_str = arguments.get("date_str")
            if date_str:
                try:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    target_date = date.today()
            else:
                target_date = date.today()
            return get_dashboard_kpis(org, target_date)
            
        elif name == "get_price_drift":
            return calculate_price_drift(org)
            
        elif name == "get_stop_lists":
            stop_lists = StopListHistory.objects.filter(organization=org).order_by('-started_at')[:10]
            return StopListHistorySerializer(stop_lists, many=True).data
            
        elif name == "list_available_reports":
            from apps.analytics.models import IikoOlapPreset
            presets = IikoOlapPreset.objects.filter(organization=org)
            res = []
            for p in presets:
                res.append({
                    "id": p.id,
                    "preset_id": str(p.preset_id),
                    "name": p.name,
                    "description": p.description,
                    "is_system": p.is_system,
                    "report_type_key": p.report_type_key
                })
            return res
            
        elif name == "get_report_data":
            preset_uuid = arguments.get("preset_id")
            from_str = arguments.get("date_from")
            to_str = arguments.get("date_to")
            
            if not preset_uuid or not from_str or not to_str:
                return {"error": "Параметры preset_id, date_from и date_to обязательны."}
                
            try:
                from_date = datetime.strptime(from_str, "%Y-%m-%d").date()
                to_date = datetime.strptime(to_str, "%Y-%m-%d").date()
            except ValueError:
                return {"error": "Неверный формат дат. Используйте YYYY-MM-DD."}
                
            from apps.analytics.services import IikoOlapService
            olap_service = IikoOlapService(org)
            return olap_service.get_olap_by_preset(preset_uuid, from_date, to_date)

        elif name == "list_tables":
            return {"tables": sorted(list(ALLOWED_VIEWS))}

        elif name == "get_table_schema":
            table_name = arguments.get("table_name", "")
            if not table_name:
                return {"error": "Параметр table_name обязателен"}
            if table_name not in ALLOWED_VIEWS:
                return {"error": f"Доступ к таблице '{table_name}' запрещен. Разрешены только: {', '.join(ALLOWED_VIEWS)}"}
            
            from django.db import connection
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    schema = {row[1]: row[2] for row in cursor.fetchall()}
                else:
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s
                    """, [table_name])
                    schema = {row[0]: row[1] for row in cursor.fetchall()}
            return {"table": table_name, "columns": schema}

        elif name == "execute_sql_query":
            query = arguments.get("query", "")
            if not query:
                return {"error": "Параметр query обязателен"}
            
            try:
                rewritten_query = rewrite_and_validate_sql(query, org.id)
            except ValueError as ve:
                return {"error": str(ve)}
            except Exception as e:
                return {"error": f"Ошибка безопасности или парсинга SQL: {str(e)}"}
                
            from django.db import connection
            with connection.cursor() as cursor:
                try:
                    cursor.execute(rewritten_query)
                    columns = [col[0] for col in cursor.description]
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return {"results": results}
                except Exception as e:
                    return {"error": str(e)}
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return {"error": str(e)}
        
    return {"error": "Tool not found"}



class LLMService:
    def __init__(self, organization: Organization):
        self.org = organization
        self.provider = organization.llm_provider
        self.model = organization.llm_model_name
        self.api_key = organization.llm_api_key
        
        semantic_prompt = """
Вы — полезный AI-финансовый аналитик ресторана. Вам доступен прямой SQL-доступ к базе данных, но исключительно через следующие 4 аналитических представления (SQL Views). Имена таблиц в БД совпадают с именами представлений:

1. `v_ai_daily_sales` — агрегированные дневные продажи и KPI:
   - `date` (DATE): дата отчета
   - `revenue` (DECIMAL): выручка (общие продажи за день)
   - `cost` (DECIMAL): себестоимость проданных товаров (фудкост в деньгах)
   - `discounts` (DECIMAL): сумма предоставленных скидок
   - `checks_count` (INTEGER): количество чеков/транзакций за день
   - `guests_count` (INTEGER): количество обслуженных гостей

2. `v_ai_payment_types` — продажи в разрезе типов оплаты:
   - `date` (DATE): дата отчета
   - `payment_type` (VARCHAR): тип оплаты (например, "Карта", "Наличные", "Kaspi QR", "iikoCard")
   - `revenue` (DECIMAL): сумма выручки по данному типу оплаты
   - `checks_count` (INTEGER): количество транзакций/чеков этого типа оплаты

3. `v_ai_stop_list` — упущенная выручка из-за нахождения блюд в стоп-листах:
   - `product_name` (VARCHAR): название блюда
   - `started_at` (TIMESTAMP): время добавления в стоп-лист
   - `ended_at` (TIMESTAMP): время удаления из стоп-листа (может быть null, если блюдо все еще в стопе)
   - `duration_seconds` (INTEGER): время простоя в секундах
   - `lost_revenue` (DECIMAL): упущенная выручка за время простоя
   - `lost_profit` (DECIMAL): упущенная валовая прибыль за время простоя

4. `v_ai_product_purchases` — история закупок ингредиентов у поставщиков:
   - `product_name` (VARCHAR): название закупаемого ингредиента/товара
   - `supplier_name` (VARCHAR): название поставщика (может быть null)
   - `price` (DECIMAL): цена закупа за единицу товара
   - `quantity` (DECIMAL): количество закупленного товара
   - `date` (DATE): дата прихода товара/закупки

Правила работы:
- Вы можете выполнять ТОЛЬКО SELECT-запросы к этим представлениям с помощью инструмента `execute_sql_query`.
- Вся фильтрация по вашей организации (organization_id) происходит автоматически на бэкенде. Вам НЕ нужно фильтровать по organization_id, поля organization_id скрыты от вас и отсутствуют в представлениях.
- Если для ответа на сложный вопрос вам нужно выполнить несколько шагов (например, сначала посмотреть общую выручку по дням, потом проанализировать типы оплаты или закупки конкретного подорожавшего сырья), делайте это последовательно в цикле вызовов функций.
- Если пользователю требуется наглядная визуализация данных (например, динамика выручки, структура оплат по категориям, топ подорожавших товаров), вы ДОЛЖНЫ вернуть ответ строго в формате JSON, содержащем текстовое описание и структуру данных для графика.

Формат ответа с графиком (JSON):
```json
{
  "text": "Ваш аналитический ответ и выводы на русском языке...",
  "chart": {
    "type": "bar", // или "line", "pie"
    "title": "Понятное название графика",
    "data": [
      {"label": "Подпись 1", "value": 150000},
      {"label": "Подпись 2", "value": 240000}
    ]
  }
}
```
Если график не требуется или для него нет достаточных данных, вы можете вернуть обычный текст (не в формате JSON).
"""
        self.system_prompt = (organization.llm_system_prompt or "Вы — полезный AI-финансовый аналитик.") + "\n\n" + semantic_prompt

    def _call_openai_compatible(self, url: str, messages: list, tools: list = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Clean messages payload for OpenAI API requirements.
        # OpenAI compatibility layers (e.g. DeepSeek) might require tool messages to have tool_call_id.
        payload_messages = []
        for msg in messages:
            clean_msg = {"role": msg["role"]}
            if msg.get("content") is not None:
                clean_msg["content"] = msg["content"]
            else:
                clean_msg["content"] = None
                
            if msg.get("tool_calls"):
                clean_msg["tool_calls"] = msg["tool_calls"]
            if msg.get("tool_call_id"):
                clean_msg["tool_call_id"] = msg["tool_call_id"]
            if msg.get("name"):
                clean_msg["name"] = msg["name"]
            payload_messages.append(clean_msg)

        payload = {
            "model": self.model or ("gpt-4o-mini" if "openai" in url else "deepseek-chat"),
            "messages": payload_messages
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            
        with httpx.Client(timeout=45) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def _call_gemini(self, messages: list, tools: list = None) -> dict:
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                # system prompt is passed in systemInstruction
                continue
                
            if msg["role"] == "assistant":
                parts = []
                if msg.get("content"):
                    parts.append({"text": msg["content"]})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        parts.append({
                            "functionCall": {
                                "name": tc["function"]["name"],
                                "args": json.loads(tc["function"]["arguments"])
                            }
                        })
                contents.append({
                    "role": "model",
                    "parts": parts if parts else [{"text": ""}]
                })
            elif msg["role"] == "tool":
                try:
                    tool_res_obj = json.loads(msg["content"])
                except Exception:
                    tool_res_obj = {"result": msg["content"]}
                if not isinstance(tool_res_obj, dict):
                    tool_res_obj = {"result": tool_res_obj}
                    
                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.get("name"),
                            "response": tool_res_obj
                        }
                    }]
                })
            else:
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.get("content", "")}]
                })
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model or 'gemini-1.5-flash'}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": self.system_prompt}]
            }
        }
        
        if tools:
            declarations = []
            for t in tools:
                func = t["function"]
                declarations.append({
                    "name": func["name"],
                    "description": func["description"],
                    "parameters": func.get("parameters", {})
                })
            payload["tools"] = [{"functionDeclarations": declarations}]
            
        with httpx.Client(timeout=45) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            res_json = response.json()
            
            candidate = res_json.get("candidates", [{}])[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [{}])
            
            text = ""
            tool_calls = []
            
            for i, part in enumerate(parts):
                if "text" in part:
                    text = part["text"]
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append({
                        "id": f"gemini_tool_{i}",
                        "type": "function",
                        "function": {
                            "name": fc["name"],
                            "arguments": json.dumps(fc.get("args", {}))
                        }
                    })
                    
            choice = {
                "message": {
                    "role": "assistant",
                    "content": text
                }
            }
            if tool_calls:
                choice["message"]["tool_calls"] = tool_calls
                
            return {"choices": [choice]}

    def _call_anthropic(self, messages: list, tools: list = None) -> dict:
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                continue
            
            role = msg["role"]
            if role == "assistant":
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        content.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                        })
                claude_messages.append({
                    "role": "assistant",
                    "content": content if content else [{"type": "text", "text": ""}]
                })
            elif role == "tool":
                claude_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": msg["content"]
                    }]
                })
            else:
                claude_messages.append({
                    "role": "user",
                    "content": msg.get("content", "")
                })
            
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "system": self.system_prompt,
            "messages": claude_messages,
            "max_tokens": 4000
        }
        
        if tools:
            claude_tools = []
            for t in tools:
                func = t["function"]
                claude_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func.get("parameters", {})
                })
            payload["tools"] = claude_tools
            
        with httpx.Client(timeout=45) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            res_json = response.json()
            
            content_list = res_json.get("content", [])
            text = ""
            tool_calls = []
            
            for item in content_list:
                if item["type"] == "text":
                    text = item["text"]
                elif item["type"] == "tool_use":
                    tool_calls.append({
                        "id": item["id"],
                        "type": "function",
                        "function": {
                            "name": item["name"],
                            "arguments": json.dumps(item["input"])
                        }
                    })
                    
            choice = {
                "message": {
                    "role": "assistant",
                    "content": text
                }
            }
            if tool_calls:
                choice["message"]["tool_calls"] = tool_calls
                
            return {"choices": [choice]}

    def run_chat(self, history: list, user=None) -> dict:
        """
        Runs chat completion with history in a ReAct loop and returns a structured response dict.
        """
        if not self.api_key:
            return {"response": "Ошибка: В настройках LLM не указан API-ключ!", "chart": None}
            
        messages = [{"role": "system", "content": self.system_prompt}] + history
        
        max_steps = 5
        step = 0
        
        try:
            while step < max_steps:
                # Force text response on the last step by removing tools
                current_tools = TOOLS if step < max_steps - 1 else None
                
                if self.provider == "openai":
                    url = "https://api.openai.com/v1/chat/completions"
                    res = self._call_openai_compatible(url, messages, current_tools)
                elif self.provider == "deepseek":
                    url = "https://api.deepseek.com/chat/completions"
                    res = self._call_openai_compatible(url, messages, current_tools)
                elif self.provider == "gemini":
                    res = self._call_gemini(messages, current_tools)
                elif self.provider == "anthropic":
                    res = self._call_anthropic(messages, current_tools)
                else:
                    return {"response": f"Ошибка: Неизвестный LLM провайдер '{self.provider}'", "chart": None}
                    
                choice = res["choices"][0]
                message = choice["message"]
                tool_calls = message.get("tool_calls")
                
                if not tool_calls:
                    final_text = message.get("content") or ""
                    return parse_agent_response(final_text)
                    
                # Append assistant's intent to call tools to history
                # We need to ensure message is a dictionary with role: 'assistant'
                clean_assistant_msg = {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls
                }
                messages.append(clean_assistant_msg)
                
                # Execute all requested tool calls
                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    tool_args = json.loads(tc["function"]["arguments"])
                    
                    tool_result = execute_tool(self.org, tool_name, tool_args, user=user)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                    
                step += 1
                
            return {"response": "Ошибка: Превышен лимит шагов рассуждения (ReAct loop limit).", "chart": None}
            
        except Exception as e:
            logger.error(f"Error calling LLM provider {self.provider}: {e}", exc_info=True)
            return {"response": f"Ошибка при обращении к AI-модели ({self.provider}): {str(e)}", "chart": None}

