import re
import random
import datetime
import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from apps.core.models import Organization, PosTerminal
from apps.loyalty.models import Customer, TerminalPaymentOtp
from apps.loyalty.views import send_telegram_message

logger = logging.getLogger(__name__)


def get_org_from_secret(request) -> Organization:
    """
    Validates X-Terminal-Secret header and returns Organization or None.
    """
    secret = request.headers.get('X-Terminal-Secret') or request.META.get('HTTP_X_TERMINAL_SECRET')
    if not secret:
        # Also check Authorization Bearer fallback
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            secret = auth_header.replace('Bearer ', '').strip()

    if not secret:
        return None

    return Organization.objects.filter(terminal_secret=secret).first()


def normalize_phone(raw_phone: str) -> str:
    """
    Normalizes phone string to international E.164-like format +7XXXXXXXXXX.
    """
    if not raw_phone:
        return ""
    digits = re.sub(r'\D', '', str(raw_phone))
    if digits.startswith('8') and len(digits) == 11:
        return '+7' + digits[1:]
    elif len(digits) == 10:
        return '+7' + digits
    elif len(digits) == 11 and digits.startswith('7'):
        return '+' + digits
    elif digits:
        return '+' + digits
    return ""


def mask_phone(phone: str) -> str:
    """
    Formats phone for cashier display, e.g. +7 701 *** 45 67.
    """
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11:
        return f"+{digits[0]} {digits[1:4]} *** {digits[7:9]} {digits[9:]}"
    return phone[:4] + "***" + phone[-2:] if len(phone) > 6 else phone


class TerminalPingView(APIView):
    """
    Heartbeat endpoint called by iikoFront plugin every 2-3 minutes.
    Registers terminal if not known, updates last_seen_at and IP.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        org = get_org_from_secret(request)
        if not org:
            return Response(
                {"error": "Неверный или отсутствующий секретный ключ терминала (X-Terminal-Secret)"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        terminal_id = request.data.get('terminal_id')
        terminal_name = request.data.get('terminal_name') or "Касса iikoFront"
        plugin_version = request.data.get('plugin_version') or ""
        iiko_version = request.data.get('iiko_version') or ""
        
        # Get client IP
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        client_ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR')
        local_ip = request.data.get('ip_address') or client_ip

        if not terminal_id:
            return Response({"error": "Параметр 'terminal_id' обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        terminal, created = PosTerminal.objects.update_or_create(
            organization=org,
            terminal_id=terminal_id,
            defaults={
                'name': terminal_name,
                'plugin_version': plugin_version,
                'iiko_version': iiko_version,
                'ip_address': local_ip,
                'last_seen_at': timezone.now()
            }
        )

        return Response({
            "status": "ok",
            "terminal_id": str(terminal.terminal_id),
            "terminal_name": terminal.name,
            "is_active": terminal.is_active,
            "org_is_active": org.is_active,
            "is_bonus_confirmation_enabled": org.is_bonus_confirmation_enabled
        })


class TerminalRequestCodeView(APIView):
    """
    Endpoint called when cashier selects bonus payment on iikoFront.
    Generates 4-digit OTP, cascades via Telegram -> WhatsApp, returns session_id.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        org = get_org_from_secret(request)
        if not org:
            return Response(
                {"error": "Неверный или отсутствующий секретный ключ терминала (X-Terminal-Secret)"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 1. Check organization active license
        if not org.is_active:
            return Response({
                "status": "error",
                "error_code": "LICENSE_EXPIRED",
                "message": "Лицензия сервиса лояльности не активна. Пожалуйста, обратитесь к администратору для продления."
            }, status=status.HTTP_403_FORBIDDEN)

        # 2. Check bonus confirmation module
        if not org.is_bonus_confirmation_enabled:
            return Response({
                "status": "error",
                "error_code": "MODULE_DISABLED",
                "message": "Модуль подтверждения списания бонусов не активирован для данного заведения."
            }, status=status.HTTP_403_FORBIDDEN)

        # 3. Check terminal activation
        terminal_id = request.data.get('terminal_id')
        terminal_name = request.data.get('terminal_name') or "Касса"
        if not terminal_id:
            return Response({"error": "Параметр 'terminal_id' обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        terminal, _ = PosTerminal.objects.get_or_create(
            organization=org,
            terminal_id=terminal_id,
            defaults={'name': terminal_name, 'is_active': False}
        )
        terminal.last_seen_at = timezone.now()
        terminal.save(update_fields=['last_seen_at'])

        if not terminal.is_active:
            return Response({
                "status": "error",
                "error_code": "TERMINAL_NOT_ACTIVATED",
                "message": f"Терминал «{terminal.name}» не активирован. Обратитесь к администратору для включения лицензии кассы."
            }, status=status.HTTP_403_FORBIDDEN)

        # 4. Resolve customer & phone
        raw_phone = request.data.get('phone')
        iiko_customer_id = request.data.get('iiko_customer_id')
        customer = None

        if raw_phone:
            clean_phone = normalize_phone(raw_phone)
            customer = Customer.objects.filter(organization=org, phone=clean_phone).first()
        elif iiko_customer_id:
            customer = Customer.objects.filter(organization=org, iiko_customer_id=iiko_customer_id).first()
            clean_phone = customer.phone if customer else ""
        else:
            return Response({
                "status": "error",
                "error_code": "PHONE_REQUIRED",
                "message": "Не указан номер телефона клиента для отправки кода подтверждения."
            }, status=status.HTTP_400_BAD_REQUEST)

        if not clean_phone:
            return Response({
                "status": "error",
                "error_code": "PHONE_REQUIRED",
                "message": "Не удалось определить номер телефона гостя."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Rate-limiting: max 1 code per 30 seconds per phone
        cutoff = timezone.now() - datetime.timedelta(seconds=30)
        recent_otp = TerminalPaymentOtp.objects.filter(
            organization=org, phone=clean_phone, created_at__gte=cutoff
        ).first()
        if recent_otp:
            return Response({
                "status": "error",
                "error_code": "RATE_LIMITED",
                "message": "Код уже отправлен. Подождите 30 секунд перед повторным запросом.",
                "timeout": 30
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 5. Generate 4-digit code
        code = f"{random.randint(1000, 9999)}"
        amount = request.data.get('amount') or 0.00
        order_id = str(request.data.get('order_id') or '')

        otp = TerminalPaymentOtp.objects.create(
            organization=org,
            terminal=terminal,
            customer=customer,
            phone=clean_phone,
            code=code,
            amount=amount,
            order_id=order_id,
            expires_at=timezone.now() + datetime.timedelta(seconds=180)
        )

        # 6. Cascading delivery: Telegram -> WhatsApp
        channel = None
        delivery_error = None

        # Priority 1: Telegram
        if customer and customer.telegram_id and org.tg_bot_token:
            try:
                text = (
                    f"🔐 Код подтверждения оплаты бонусами: {code}\n"
                    f"Сумма списания: {amount} бонусов\n"
                    f"Заведение: {org.name}\n\n"
                    f"Никому не сообщайте этот код, кроме кассира."
                )
                send_telegram_message(org.tg_bot_token, customer.telegram_id, text)
                channel = "telegram"
                logger.info(f"Terminal OTP {code} sent via Telegram to {customer.telegram_id} (org {org.slug})")
            except Exception as e:
                logger.error(f"Failed to send Telegram OTP: {e}")
                delivery_error = str(e)

        # Priority 2: WhatsApp (WABA)
        if not channel and org.is_waba_configured:
            try:
                from apps.core.services.waba_service import dispatch_waba_notification
                waba_payload = {
                    'phone': clean_phone,
                    'text': code,
                    'auth_code': code,
                    'amount': str(amount),
                    'org_name': org.name
                }
                results = dispatch_waba_notification(
                    org=org,
                    event_type='auth_code',
                    actual_payload=waba_payload,
                    recipient_phone=clean_phone
                )
                # Check for delivery issues
                channel = "whatsapp"
                logger.info(f"Terminal OTP {code} sent via WhatsApp to {clean_phone} (org {org.slug})")
            except Exception as e:
                logger.error(f"Failed to send WABA OTP: {e}")
                delivery_error = str(e)

        if not channel:
            otp.delete()
            return Response({
                "status": "error",
                "error_code": "NO_DELIVERY_CHANNEL",
                "message": "У гостя не подключен Telegram-бот и не настроен WhatsApp для отправки кода подтверждения."
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "status": "success",
            "session_id": str(otp.session_id),
            "channel": channel,
            "phone_masked": mask_phone(clean_phone),
            "expires_in_seconds": 180
        })


class TerminalVerifyCodeView(APIView):
    """
    Endpoint called when cashier submits the 4-digit OTP.
    Validates code, checks attempts limit and expiration.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        org = get_org_from_secret(request)
        if not org:
            return Response(
                {"error": "Неверный или отсутствующий секретный ключ терминала (X-Terminal-Secret)"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not org.is_active:
            return Response({
                "status": "error",
                "error_code": "LICENSE_EXPIRED",
                "message": "Лицензия сервиса лояльности не активна."
            }, status=status.HTTP_403_FORBIDDEN)

        session_id = request.data.get('session_id')
        entered_code = str(request.data.get('code') or '').strip()

        if not session_id or not entered_code:
            return Response(
                {"error": "Параметры 'session_id' и 'code' обязательны"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = TerminalPaymentOtp.objects.filter(organization=org, session_id=session_id).first()
        if not otp:
            return Response({
                "status": "error",
                "error_code": "SESSION_NOT_FOUND",
                "message": "Сессия проверки не найдена. Запросите код заново."
            }, status=status.HTTP_404_NOT_FOUND)

        if otp.is_verified:
            return Response({
                "status": "error",
                "error_code": "ALREADY_VERIFIED",
                "message": "Данный код уже был успешно использован."
            }, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > otp.expires_at:
            return Response({
                "status": "error",
                "error_code": "CODE_EXPIRED",
                "message": "Срок действия кода истек. Запросите новый код."
            }, status=status.HTTP_400_BAD_REQUEST)

        if otp.attempts >= 3:
            return Response({
                "status": "error",
                "error_code": "TOO_MANY_ATTEMPTS",
                "message": "Превышено максимальное число попыток ввода (3). Запросите новый код."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate code match
        if otp.code != entered_code:
            otp.attempts += 1
            otp.save(update_fields=['attempts'])
            remaining = max(0, 3 - otp.attempts)
            return Response({
                "status": "error",
                "error_code": "INVALID_CODE",
                "verified": False,
                "message": f"Неверный код подтверждения. Осталось попыток: {remaining}",
                "remaining_attempts": remaining
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verification successful
        otp.is_verified = True
        otp.save(update_fields=['is_verified'])

        return Response({
            "status": "success",
            "verified": True,
            "message": "Код успешно подтвержден. Оплата бонусами разрешена."
        })
