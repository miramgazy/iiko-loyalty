import logging
import re
import requests
from typing import Dict, Any, Optional
from apps.core.models import Organization

logger = logging.getLogger(__name__)


class SmscService:
    """
    Service for sending SMS notifications via SMS-Center (smsc.kz / smsc.ru).
    Official API docs: https://smsc.kz/api/
    """
    PRIMARY_URL = "https://smsc.kz/sys/send.php"
    FALLBACK_URL = "https://smsc.ru/sys/send.php"
    BALANCE_PRIMARY_URL = "https://smsc.kz/sys/balance.php"
    BALANCE_FALLBACK_URL = "https://smsc.ru/sys/balance.php"

    def __init__(self, organization: Organization):
        self.org = organization
        self.login = organization.smsc_login.strip() if organization.smsc_login else ""
        self.password = organization.smsc_password.strip() if organization.smsc_password else ""
        self.sender = organization.smsc_sender.strip() if organization.smsc_sender else ""

    def is_configured(self) -> bool:
        return bool(self.org.is_smsc_enabled and self.login and self.password)

    def normalize_phone_for_smsc(self, phone: str) -> str:
        """
        Normalizes phone to digits without +, e.g. 77011234567.
        """
        digits = re.sub(r'\D', '', str(phone or ''))
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]
        return digits

    def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """
        Sends an SMS message to recipient phone.
        Returns dict with success: bool, id, cost, balance, error.
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "SMS-Центр не настроен или выключен для данной организации",
                "error_code": "NOT_CONFIGURED"
            }

        clean_phone = self.normalize_phone_for_smsc(phone)
        if len(clean_phone) < 11:
            return {
                "success": False,
                "error": f"Некорректный номер телефона: {phone}",
                "error_code": "INVALID_PHONE"
            }

        params = {
            "login": self.login,
            "psw": self.password,
            "phones": clean_phone,
            "mes": message,
            "fmt": 3,  # JSON format
            "charset": "utf-8"
        }
        if self.sender:
            params["sender"] = self.sender

        urls = [self.PRIMARY_URL, self.FALLBACK_URL]
        last_error = None

        for url in urls:
            try:
                response = requests.post(url, data=params, timeout=12)
                if response.status_code == 200:
                    data = response.json()
                    # Check for SMSC error in payload
                    if "error" in data or "error_code" in data:
                        err_code = data.get("error_code")
                        err_msg = data.get("error", "Неизвестная ошибка SMSC")
                        logger.error(f"[SMSC] Error sending SMS to {clean_phone} (org {self.org.slug}): #{err_code} {err_msg}")
                        return {
                            "success": False,
                            "error": f"Ошибка SMSC #{err_code}: {err_msg}",
                            "error_code": err_code
                        }

                    msg_id = data.get("id")
                    cost = data.get("cost")
                    balance = data.get("balance")
                    logger.info(f"[SMSC] Successfully sent SMS to {clean_phone} (id={msg_id}, cost={cost}, org={self.org.slug})")
                    return {
                        "success": True,
                        "message_id": msg_id,
                        "cost": cost,
                        "balance": balance
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
            except Exception as e:
                last_error = str(e)
                logger.warning(f"[SMSC] Request to {url} failed: {e}. Trying fallback if available.")

        return {
            "success": False,
            "error": f"Не удалось отправить SMS через SMSC: {last_error}",
            "error_code": "NETWORK_ERROR"
        }

    def get_balance(self) -> Dict[str, Any]:
        """
        Retrieves current account balance from SMSC.
        """
        if not self.login or not self.password:
            return {"success": False, "error": "Логин или пароль SMSC не указаны"}

        params = {
            "login": self.login,
            "psw": self.password,
            "fmt": 3,
            "charset": "utf-8"
        }

        urls = [self.BALANCE_PRIMARY_URL, self.BALANCE_FALLBACK_URL]
        for url in urls:
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data or "error_code" in data:
                        return {
                            "success": False,
                            "error": f"Ошибка SMSC #{data.get('error_code')}: {data.get('error')}"
                        }
                    return {
                        "success": True,
                        "balance": data.get("balance"),
                        "currency": data.get("currency", "KZT")
                    }
            except Exception as e:
                logger.warning(f"[SMSC] Balance check at {url} failed: {e}")

        return {"success": False, "error": "Не удалось связаться с сервером SMSC"}


def send_sms_otp(org: Organization, phone: str, code: str, amount: float = 0.0) -> Dict[str, Any]:
    """
    Helper to send a payment confirmation OTP via SMS-Center.
    """
    service = SmscService(org)
    if not service.is_configured():
        return {
            "success": False,
            "error": "SMS-Центр выключен или не настроен для данной организации",
            "error_code": "NOT_CONFIGURED"
        }

    org_name = org.name or "MadiTech Loyalty"
    text = f"{org_name}: Код подтверждения оплаты бонусами {code}. Сумма списания: {amount} б."
    return service.send_sms(phone, text)

