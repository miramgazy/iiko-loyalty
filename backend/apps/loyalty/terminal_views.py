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
        clean_phone = ""

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

        # If customer not in local DB, auto-import from iikoCard / iiko Cloud Loyalty
        try:
            from apps.loyalty.services import IikoLoyaltyService
            from apps.loyalty.models import CustomerWallet
            from datetime import datetime
            service = IikoLoyaltyService(org)

            guest_info = None
            if clean_phone:
                guest_info = service.get_customer_info_by_phone(clean_phone)
            elif iiko_customer_id:
                guest_info = service.get_customer_info_by_id(iiko_customer_id)

            if guest_info and guest_info.get("id"):
                iiko_id = guest_info.get("id")
                guest_phone = guest_info.get("phone") or clean_phone
                if not clean_phone and guest_phone:
                    clean_phone = normalize_phone(guest_phone)

                cards = guest_info.get("cards", [])
                card_num = str(cards[0].get("number")) if cards and cards[0].get("number") else ""

                bday_str = guest_info.get("birthday")
                parsed_bday = None
                if bday_str and len(bday_str) >= 10:
                    try:
                        parsed_bday = datetime.strptime(bday_str[:10], '%Y-%m-%d').date()
                    except Exception:
                        pass

                wallet_balances = guest_info.get("walletBalances", [])
                total_balance = 0.0
                for w in wallet_balances:
                    if w.get("type") == 1:
                        total_balance += float(w.get("balance", 0))

                if not customer:
                    customer = Customer.objects.create(
                        organization=org,
                        phone=clean_phone,
                        iiko_customer_id=iiko_id,
                        first_name=guest_info.get("name") or "",
                        last_name=guest_info.get("surname") or "",
                        email=guest_info.get("email") or "",
                        birthday=parsed_bday,
                        iiko_card_number=card_num,
                        loyalty_balance=total_balance,
                        is_pushed_to_iiko=True,
                        onboarding_source='iiko_terminal'
                    )

                    for w in wallet_balances:
                        w_id = w.get("id")
                        if w_id:
                            CustomerWallet.objects.create(
                                customer=customer,
                                wallet_id=w_id,
                                name=w.get("name") or "Кошелек лояльности",
                                balance=float(w.get("balance", 0)),
                                wallet_type=w.get("type", 1)
                            )

                    logger.info(f"[TerminalRequestCode] Auto-imported customer {customer.id} ('{customer.first_name}', phone={clean_phone}) from iikoCard for org {org.slug}")
                else:
                    # Refresh existing customer's balance & name from iikoCard
                    updated = []
                    if float(customer.loyalty_balance) != total_balance:
                        customer.loyalty_balance = total_balance
                        updated.append('loyalty_balance')
                    remote_name = guest_info.get("name") or ""
                    if remote_name and not customer.first_name:
                        customer.first_name = remote_name
                        updated.append('first_name')
                    if updated:
                        customer.save(update_fields=updated)

                if customer:
                    from apps.loyalty.utils import ensure_customer_card_in_iiko
                    ensure_customer_card_in_iiko(customer, service=service, guest_info=guest_info)
        except Exception as e:
            logger.warning(f"[TerminalRequestCode] Error checking/importing customer from iikoCard: {e}")

        customer_balance = float(customer.loyalty_balance) if customer else 0.0
        customer_name = f"{customer.first_name} {customer.last_name}".strip() if customer else "Гость"
        if not customer_name:
            customer_name = "Гость"

        if not clean_phone:
            return Response({
                "status": "error",
                "error_code": "PHONE_REQUIRED",
                "message": "Не удалось определить номер телефона гостя."
            }, status=status.HTTP_400_BAD_REQUEST)

        amount = float(request.data.get('amount') or 0.00)
        order_id = str(request.data.get('order_id') or '')

        # Check balance sufficiency if customer found
        if customer and amount > 0 and customer_balance < amount:
            return Response({
                "status": "error",
                "error_code": "INSUFFICIENT_BALANCE",
                "message": f"Недостаточно бонусов. Доступно: {customer_balance:.0f} Б, запрошено к списанию: {amount:.0f} Б.",
                "balance": customer_balance,
                "customer_name": customer_name
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
                "timeout": 30,
                "balance": customer_balance,
                "customer_name": customer_name
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 5. Generate 4-digit code
        code = f"{random.randint(1000, 9999)}"

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

        # 6. Cascading delivery: Telegram -> WhatsApp -> SMS-Center
        channel = None
        delivery_error = None
        not_on_whatsapp = False

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

                waba_success = False
                if results and any(r.get('success') for r in results):
                    waba_success = True
                else:
                    for r in results:
                        if r.get('is_not_on_whatsapp'):
                            not_on_whatsapp = True
                            break
                        err_msg = str(r.get('error') or '').lower()
                        if 'not on whatsapp' in err_msg or 'not a valid whatsapp user' in err_msg or '131026' in err_msg:
                            not_on_whatsapp = True
                            break

                if waba_success:
                    channel = "whatsapp"
                    logger.info(f"Terminal OTP {code} sent via WhatsApp to {clean_phone} (org {org.slug})")
                else:
                    delivery_error = results[0].get('error') if results else "WABA rules not configured or message failed"
                    logger.warning(f"WABA OTP dispatch did not succeed for {clean_phone}: {delivery_error} (not_on_whatsapp={not_on_whatsapp})")
            except Exception as e:
                logger.error(f"Failed to send WABA OTP: {e}")
                delivery_error = str(e)

        # Priority 3: SMS-Center (SMSC)
        if not channel and org.is_smsc_configured:
            try:
                from apps.core.services.sms_service import send_sms_otp
                sms_res = send_sms_otp(org=org, phone=clean_phone, code=code, amount=float(amount))
                if sms_res.get('success'):
                    channel = "sms"
                    logger.info(f"Terminal OTP {code} sent via SMSC to {clean_phone} (id={sms_res.get('message_id')}, org {org.slug})")
                else:
                    logger.warning(f"SMSC OTP dispatch failed for {clean_phone}: {sms_res.get('error')}")
                    delivery_error = sms_res.get('error')
            except Exception as e:
                logger.error(f"Failed to send SMS OTP via SMSC: {e}")
                delivery_error = str(e)

        if not channel:
            otp.delete()
            if not_on_whatsapp:
                return Response({
                    "status": "error",
                    "error_code": "NO_WHATSAPP",
                    "message": f"У клиента с номером {mask_phone(clean_phone)} нет WhatsApp. Не удалось доставить код подтверждения."
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "status": "error",
                "error_code": "NO_DELIVERY_CHANNEL",
                "message": delivery_error or "У гостя не подключен Telegram-бот и не удалось отправить код через WhatsApp или SMS."
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "status": "success",
            "session_id": str(otp.session_id),
            "channel": channel,
            "phone_masked": mask_phone(clean_phone),
            "expires_in_seconds": 180,
            "balance": customer_balance,
            "customer_name": customer_name
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

        customer_bal = float(otp.customer.loyalty_balance) if otp.customer else 0.0
        customer_nm = f"{otp.customer.first_name} {otp.customer.last_name}".strip() if otp.customer else "Гость"

        return Response({
            "status": "success",
            "verified": True,
            "message": "Код успешно подтвержден. Оплата бонусами разрешена.",
            "balance": customer_bal,
            "customer_name": customer_nm or "Гость"
        })


class TerminalCustomerInfoView(APIView):
    """
    Endpoint for POS terminal to query customer balance, card, and name by phone number.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        org = get_org_from_secret(request)
        if not org:
            return Response(
                {"error": "Неверный или отсутствующий секретный ключ терминала (X-Terminal-Secret)"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        raw_phone = request.data.get('phone') or ""
        clean_phone = normalize_phone(raw_phone) if raw_phone else ""
        if not clean_phone:
            return Response({"error": "Параметр 'phone' обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        customer = Customer.objects.filter(organization=org, phone=clean_phone).first()

        try:
            from apps.loyalty.services import IikoLoyaltyService
            service = IikoLoyaltyService(org)
            guest_info = service.get_customer_info_by_phone(clean_phone)
            if guest_info and guest_info.get("id"):
                wallet_balances = guest_info.get("walletBalances", [])
                total_balance = 0.0
                for w in wallet_balances:
                    if w.get("type") == 1:
                        total_balance += float(w.get("balance", 0))

                if not customer:
                    iiko_id = guest_info.get("id")
                    cards = guest_info.get("cards", [])
                    card_num = str(cards[0].get("number")) if cards and cards[0].get("number") else ""

                    customer = Customer.objects.create(
                        organization=org,
                        phone=clean_phone,
                        iiko_customer_id=iiko_id,
                        first_name=guest_info.get("name") or "",
                        last_name=guest_info.get("surname") or "",
                        email=guest_info.get("email") or "",
                        iiko_card_number=card_num,
                        loyalty_balance=total_balance,
                        is_pushed_to_iiko=True,
                        onboarding_source='iiko_terminal'
                    )
                else:
                    customer.loyalty_balance = total_balance
                    remote_name = guest_info.get("name") or ""
                    if remote_name and not customer.first_name:
                        customer.first_name = remote_name
                    customer.save(update_fields=['loyalty_balance', 'first_name'])

                if customer:
                    from apps.loyalty.utils import ensure_customer_card_in_iiko
                    ensure_customer_card_in_iiko(customer, service=service, guest_info=guest_info)
        except Exception as e:
            logger.warning(f"[TerminalCustomerInfo] Error fetching customer from iiko: {e}")

        if not customer:
            return Response({
                "status": "not_found",
                "found": False,
                "message": "Клиент с таким номером не найден"
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "status": "success",
            "found": True,
            "phone": customer.phone,
            "name": f"{customer.first_name} {customer.last_name}".strip() or "Гость",
            "balance": float(customer.loyalty_balance),
            "card_number": customer.iiko_card_number or "",
            "is_telegram_subscribed": bool(customer.telegram_id)
        })
