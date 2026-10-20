import re
import logging
import requests
from typing import Dict, Any, List, Optional
from apps.core.models import Organization, WabaTriggerRule, WabaMessageLog

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v19.0"
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class WabaService:
    def __init__(self, organization: Organization):
        self.organization = organization
        self.access_token = organization.waba_access_token
        self.business_account_id = organization.waba_business_account_id
        self.phone_number_id = organization.waba_phone_number_id

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def fetch_templates(self) -> List[Dict[str, Any]]:
        """
        Fetch approved / available message templates from Meta WABA.
        """
        if not self.access_token or not self.business_account_id:
            raise ValueError("WABA Access Token и Business Account ID обязательны для выгрузки шаблонов")

        url = f"{GRAPH_API_BASE_URL}/{self.business_account_id}/message_templates"
        params = {"limit": 100}

        try:
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=15)
            data = response.json()
            if response.status_code != 200:
                error_msg = data.get("error", {}).get("message", response.text)
                raise ValueError(f"Meta API Error ({response.status_code}): {error_msg}")

            return data.get("data", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch WABA templates: {e}")
            raise ValueError(f"Не удалось подключиться к Meta API: {str(e)}")

    def fetch_phone_numbers(self) -> List[Dict[str, Any]]:
        """
        Fetch registered phone numbers associated with the WABA account.
        """
        if not self.access_token or not self.business_account_id:
            raise ValueError("WABA Access Token и Business Account ID обязательны")

        url = f"{GRAPH_API_BASE_URL}/{self.business_account_id}/phone_numbers"
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            data = response.json()
            if response.status_code != 200:
                error_msg = data.get("error", {}).get("message", response.text)
                raise ValueError(f"Meta API Error ({response.status_code}): {error_msg}")

            return data.get("data", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch WABA phone numbers: {e}")
            raise ValueError(f"Не удалось подключиться к Meta API: {str(e)}")

    def resolve_value(self, source: str, static_value: str, payload_data: Dict[str, Any]) -> str:
        """
        Extract variable value according to configured source name.
        """
        if source == 'auth_code':
            text = str(payload_data.get('text', ''))
            digits = re.findall(r'\d+', text)
            return "".join(digits) if digits else ""
        elif source == 'sum':
            return str(payload_data.get('sum', '0'))
        elif source == 'sum_abs':
            val = payload_data.get('sum', 0)
            try:
                return str(abs(float(val)))
            except (ValueError, TypeError):
                return str(val)
        elif source == 'balance':
            return str(payload_data.get('balance', '0'))
        elif source == 'balance_text_smart':
            sum_val = payload_data.get('sum', 0)
            bal_val = payload_data.get('balance', 0)
            try:
                numeric_sum = float(sum_val)
                if numeric_sum >= 0:
                    return f"Ваш баланс Кошелька пополнен на: {numeric_sum} тенге. Общий баланс составляет: {bal_val} тенге."
                else:
                    return f"С Вашего баланса Кошелька списан: {abs(numeric_sum)} тенге. Общий баланс составляет: {bal_val} тенге."
            except (ValueError, TypeError):
                return f"Сумма: {sum_val}. Баланс: {bal_val}"
        elif source == 'phone':
            return str(payload_data.get('phone', ''))
        elif source == 'restaurant_name':
            return self.organization.name
        elif source == 'text':
            return str(payload_data.get('text', ''))
        elif source == 'text_line_1':
            text = str(payload_data.get('text', ''))
            lines = text.split('\n')
            return lines[0].strip() if lines else ""
        elif source == 'text_line_2':
            text = str(payload_data.get('text', ''))
            lines = text.split('\n')
            return lines[1].strip() if len(lines) > 1 else ""
        elif source == 'static':
            return static_value or ""
        return static_value or ""

    def build_components(self, parameter_mappings: Dict[str, Any], payload_data: Dict[str, Any]) -> tuple[List[Dict[str, Any]], str]:
        """
        Builds Meta Cloud API components structure and generates preview rendered text.
        """
        components = []
        preview_parts = []

        # Header component
        header_mappings = parameter_mappings.get('header', [])
        if header_mappings:
            header_params = []
            for item in header_mappings:
                val = self.resolve_value(item.get('source', ''), item.get('static_value', ''), payload_data)
                header_params.append({"type": "text", "text": val})
                preview_parts.append(f"[Header: {val}]")
            if header_params:
                components.append({
                    "type": "header",
                    "parameters": header_params
                })

        # Body component
        body_mappings = parameter_mappings.get('body', [])
        if body_mappings:
            body_params = []
            for item in body_mappings:
                val = self.resolve_value(item.get('source', ''), item.get('static_value', ''), payload_data)
                body_params.append({"type": "text", "text": val})
                preview_parts.append(f"[Body param: {val}]")
            if body_params:
                components.append({
                    "type": "body",
                    "parameters": body_params
                })

        # Button component (URL button)
        button_mappings = parameter_mappings.get('buttons', [])
        if button_mappings:
            for item in button_mappings:
                val = self.resolve_value(item.get('source', ''), item.get('static_value', ''), payload_data)
                btn_index = str(item.get('index', 0))
                components.append({
                    "type": "button",
                    "sub_type": item.get('sub_type', 'url'),
                    "index": btn_index,
                    "parameters": [
                        {"type": "text", "text": val}
                    ]
                })
                preview_parts.append(f"[Button index {btn_index}: {val}]")

        rendered_text = "\n".join(preview_parts)
        return components, rendered_text

    def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = 'ru',
        components: Optional[List[Dict[str, Any]]] = None,
        rule: Optional[WabaTriggerRule] = None,
        message_type: str = 'custom',
        rendered_text: str = ''
    ) -> Dict[str, Any]:
        """
        Sends a WhatsApp template message using Meta Cloud API and logs the result.
        """
        if not self.access_token:
            raise ValueError("WABA Access Token не настроен")
        if not self.phone_number_id:
            raise ValueError("WABA Phone Number ID не настроен")

        # Format recipient phone: extract only digits
        clean_phone = re.sub(r'\D', '', to_phone)
        if clean_phone.startswith('8') and len(clean_phone) == 11:
            clean_phone = '7' + clean_phone[1:]
        elif len(clean_phone) == 10:
            clean_phone = '7' + clean_phone

        # Prepare log record
        log = WabaMessageLog.objects.create(
            organization=self.organization,
            rule=rule,
            phone=f"+{clean_phone}" if clean_phone else to_phone,
            message_type=message_type,
            template_name=template_name,
            language=language_code,
            parameters={"components": components or []},
            rendered_text=rendered_text,
            status=WabaMessageLog.STATUS_PENDING
        )

        url = f"{GRAPH_API_BASE_URL}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            }
        }
        if components:
            payload["template"]["components"] = components

        try:
            response = requests.post(url, json=payload, headers=self.get_headers(), timeout=15)
            data = response.json()

            if response.status_code in [200, 201]:
                messages = data.get("messages", [])
                msg_id = messages[0].get("id") if messages else None
                log.waba_message_id = msg_id
                log.status = WabaMessageLog.STATUS_SENT
                log.error_message = None
                log.save(update_fields=['waba_message_id', 'status', 'error_message'])
                return {"success": True, "message_id": msg_id, "log_id": log.id}
            else:
                err_detail = data.get("error", {})
                error_msg = f"Meta Error {err_detail.get('code')}: {err_detail.get('message')}"
                log.status = WabaMessageLog.STATUS_FAILED
                log.error_message = error_msg
                log.save(update_fields=['status', 'error_message'])
                logger.error(f"WABA Send error: {error_msg}")
                return {"success": False, "error": error_msg, "log_id": log.id}

        except Exception as e:
            error_msg = str(e)
            log.status = WabaMessageLog.STATUS_FAILED
            log.error_message = error_msg
            log.save(update_fields=['status', 'error_message'])
            logger.error(f"WABA request exception: {e}")
            return {"success": False, "error": error_msg, "log_id": log.id}


def dispatch_waba_notification(
    org: Organization,
    event_type: str,
    actual_payload: Dict[str, Any],
    recipient_phone: Optional[str] = None
):
    """
    Finds enabled WabaTriggerRules matching the event_type for the organization
    and executes them via WabaService.
    """
    if not org.is_waba_enabled or not org.waba_access_token or not org.waba_phone_number_id:
        return

    phone = recipient_phone or actual_payload.get('phone')
    if not phone and actual_payload.get('customerId'):
        try:
            from apps.loyalty.models import Customer
            cust = Customer.objects.filter(organization=org, iiko_customer_id=actual_payload.get('customerId')).first()
            if cust and cust.phone:
                phone = cust.phone
        except Exception as e:
            logger.warning(f"Error looking up customer for phone resolution: {e}")

    if not phone:
        logger.info(f"WABA: No recipient phone available for event '{event_type}' in org {org.name}")
        return

    rules = WabaTriggerRule.objects.filter(organization=org, event_type=event_type, is_enabled=True)
    if not rules.exists():
        return

    service = WabaService(org)
    for rule in rules:
        try:
            components, rendered_text = service.build_components(rule.parameter_mappings, actual_payload)
            service.send_template_message(
                to_phone=str(phone),
                template_name=rule.template_name,
                language_code=rule.template_language or 'ru',
                components=components,
                rule=rule,
                message_type=rule.event_type,
                rendered_text=rendered_text
            )
        except Exception as e:
            logger.error(f"Error dispatching WABA rule '{rule.name}': {e}")


