import httpx
import json
import logging
from datetime import datetime, date
from django.conf import settings
from apps.core.models import Organization

logger = logging.getLogger(__name__)

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
            "description": "Получить список доступных таблиц в базе данных проекта (для прямого SQL-анализа).",
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
            "description": "Получить структуру и имена колонок для конкретной таблицы.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Имя таблицы (например, 'analytics_waiterolapreport')."
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
            "description": "Выполнить безопасный SQL-запрос на чтение (SELECT) к базе данных и получить результаты. Лимит вывода - 50 строк.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL-запрос (например, 'SELECT * FROM analytics_dailyolapreport WHERE organization_id = 1')."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_api_endpoint",
            "description": "Сделать HTTP-запрос к любому REST API эндпоинту бэкенда для получения данных (например, по продажам, типам оплат, официантам, клиентам или настройкам). Используйте относительные пути (начинающиеся с /api/).",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP-метод (GET или POST)."
                    },
                    "path": {
                        "type": "string",
                        "description": "Относительный путь эндпоинта (например, '/api/analytics/organizations/1/payments/')."
                    },
                    "params": {
                        "type": "object",
                        "description": "Query параметры для GET-запроса (например, {'date': '2026-08-19'})."
                    },
                    "body": {
                        "type": "object",
                        "description": "Тело запроса для POST-запроса."
                    }
                },
                "required": ["method", "path"]
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
            from django.db import connection
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                else:
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                tables = [row[0] for row in cursor.fetchall()]
            safe_tables = [t for t in tables if not any(x in t for x in ['user', 'session', 'token', 'permission'])]
            return {"tables": safe_tables}

        elif name == "get_table_schema":
            table_name = arguments.get("table_name", "")
            if not table_name:
                return {"error": "Параметр table_name обязателен"}
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
            
            upper_query = query.upper()
            forbidden = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "GRANT", "CREATE", "TRUNCATE"]
            if any(word in upper_query for word in forbidden):
                return {"error": "Ошибка безопасности: Разрешены только SELECT-запросы."}
            
            if "LIMIT" not in upper_query:
                query = query.rstrip(';') + " LIMIT 50;"
                
            from django.db import connection
            with connection.cursor() as cursor:
                try:
                    cursor.execute(query)
                    columns = [col[0] for col in cursor.description]
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return {"results": results}
                except Exception as e:
                    return {"error": str(e)}

        elif name == "call_api_endpoint":
            method = arguments.get("method", "GET").upper()
            path = arguments.get("path", "")
            params = arguments.get("params", {})
            body = arguments.get("body", {})
            
            if not path.startswith("/"):
                path = "/" + path
                
            from rest_framework.test import APIClient
            client = APIClient()
            if user:
                client.force_authenticate(user=user)
                
            try:
                if method == "GET":
                    response = client.get(path, data=params)
                elif method == "POST":
                    response = client.post(path, data=body, format='json')
                else:
                    return {"error": f"Method {method} not supported"}
                    
                try:
                    return response.json()
                except Exception:
                    return {"status_code": response.status_code, "content": response.content.decode("utf-8")}
            except Exception as e:
                return {"error": f"API request failed: {e}"}
            
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
        self.system_prompt = organization.llm_system_prompt or "Вы — полезный AI-финансовый аналитик."

    def _call_openai_compatible(self, url: str, messages: list, tools: list = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model or ("gpt-4o-mini" if "openai" in url else "deepseek-chat"),
            "messages": messages
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            
        with httpx.Client(timeout=45) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def _call_gemini(self, messages: list, tools: list = None) -> dict:
        # Convert messages to Gemini format
        # Gemini format: { "contents": [ { "role": "user"|"model", "parts": [ { "text": "..." } ] } ] }
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            if msg["role"] == "system":
                # system prompt is passed in systemInstruction
                continue
            contents.append({
                "role": role,
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
            # Format function declarations for Gemini
            declarations = []
            for t in tools:
                func = t["function"]
                # Convert OpenAI parameters schema to Gemini
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
            
            # Map Gemini response structure to OpenAI format to keep unified processing
            candidate = res_json.get("candidates", [{}])[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [{}])
            
            text = ""
            tool_calls = []
            
            for part in parts:
                if "text" in part:
                    text = part["text"]
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append({
                        "id": "gemini_tool_id",
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
        # Claude messages format (does not support system in messages array, instead in root)
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                continue
            claude_messages.append({
                "role": "assistant" if msg["role"] == "assistant" else "user",
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
            
            # Map Claude format to OpenAI-like
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

    def run_chat(self, history: list, user=None) -> str:
        """
        Runs chat completion with history and calls tools if requested.
        """
        if not self.api_key:
            return "Ошибка: В настройках LLM не указан API-ключ!"
            
        # Build messages payload
        messages = [{"role": "system", "content": self.system_prompt}] + history
        
        try:
            # 1. First invocation
            if self.provider == "openai":
                url = "https://api.openai.com/v1/chat/completions"
                res = self._call_openai_compatible(url, messages, TOOLS)
            elif self.provider == "deepseek":
                url = "https://api.deepseek.com/chat/completions"
                res = self._call_openai_compatible(url, messages, TOOLS)
            elif self.provider == "gemini":
                res = self._call_gemini(messages, TOOLS)
            elif self.provider == "anthropic":
                res = self._call_anthropic(messages, TOOLS)
            else:
                return f"Ошибка: Неизвестный LLM провайдер '{self.provider}'"
                
            choice = res["choices"][0]
            message = choice["message"]
            tool_calls = message.get("tool_calls")
            
            if not tool_calls:
                return message.get("content") or ""
                
            # 2. Handle Tool Call
            tool_call = tool_calls[0]
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            
            tool_result = execute_tool(self.org, tool_name, tool_args, user=user)
            
            # 3. Second invocation with tool results
            # For Gemini and Claude, we can just append a system instruction with the context:
            # "Пользователь запросил данные {tool_name}. Вот результат выполнения: {result}. Ответьте пользователю."
            # This is simpler and works across all LLM models without strict tool message formatting constraints.
            prompt_with_result = (
                f"\n\n[Вызов внутренней системы]: Функция '{tool_name}' с аргументами {tool_args} вернула:\n"
                f"{json.dumps(tool_result, ensure_ascii=False)}\n\n"
                f"Используйте эти данные, чтобы ответить на последний вопрос пользователя."
            )
            
            messages.append({
                "role": "system",
                "content": prompt_with_result
            })
            
            # Remove tools on the second call to force text response
            if self.provider == "openai":
                url = "https://api.openai.com/v1/chat/completions"
                res2 = self._call_openai_compatible(url, messages)
            elif self.provider == "deepseek":
                url = "https://api.deepseek.com/chat/completions"
                res2 = self._call_openai_compatible(url, messages)
            elif self.provider == "gemini":
                res2 = self._call_gemini(messages)
            elif self.provider == "anthropic":
                res2 = self._call_anthropic(messages)
                
            return res2["choices"][0]["message"].get("content") or ""
            
        except Exception as e:
            logger.error(f"Error calling LLM provider {self.provider}: {e}", exc_info=True)
            return f"Ошибка при обращении к AI-модели ({self.provider}): {str(e)}"
