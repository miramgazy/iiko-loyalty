import logging
import random
import string
from config.celery import app
from apps.loyalty.models import Customer
from apps.loyalty.services import IikoLoyaltyService
import requests

logger = logging.getLogger(__name__)

def generate_unique_card_number(organization):
    while True:
        card_number = ''.join(random.choices(string.digits, k=8))
        if card_number.startswith('0'):
            continue
        if not Customer.objects.filter(organization=organization, iiko_card_number=card_number).exists():
            return card_number

@app.task(bind=True, max_retries=5, default_retry_delay=60)
def sync_customer_to_iiko(self, customer_id, push=False):
    try:
        customer = Customer.objects.get(id=customer_id)
        if not customer.phone:
            logger.warning(f"Customer {customer_id} has no phone. Skipping sync.")
            return

        service = IikoLoyaltyService(customer.organization)

        # 1. Create or update in iiko only if missing iiko_customer_id OR if push=True
        if not customer.iiko_customer_id or push:
            birthday_str = customer.birthday.strftime('%Y-%m-%d') if customer.birthday else None
            iiko_id = service.create_or_update_customer(
                phone=customer.phone,
                first_name=customer.first_name or "Guest",
                last_name=customer.last_name,
                email=customer.email,
                birthday=birthday_str
            )

            if iiko_id and customer.iiko_customer_id != iiko_id:
                customer.iiko_customer_id = iiko_id
                customer.save(update_fields=['iiko_customer_id'])

        # 2. Get customer details to sync balance, cards, and personal details
        guest_info = service.get_customer_info_by_id(customer.iiko_customer_id)

        if guest_info:
            cards = guest_info.get("cards", [])
            if not cards:
                try:
                    logger.info(f"Customer {customer.id} has no cards in iiko. Creating virtual card...")
                    card_number = generate_unique_card_number(customer.organization)
                    service.add_virtual_card(customer.iiko_customer_id, card_number)
                    # Re-fetch guest info to get the newly created card details
                    new_guest_info = service.get_customer_info_by_id(customer.iiko_customer_id)
                    if new_guest_info:
                        guest_info = new_guest_info
                except Exception as e:
                    logger.error(f"Error registering virtual card for customer {customer.id}: {e}")

            update_fields = []

            # Sync personal details from iiko to local DB
            name = guest_info.get("name")
            if name and customer.first_name != name:
                customer.first_name = name
                update_fields.append('first_name')

            surname = guest_info.get("surname")
            if surname and customer.last_name != surname:
                customer.last_name = surname
                update_fields.append('last_name')

            email = guest_info.get("email")
            if email and customer.email != email:
                customer.email = email
                update_fields.append('email')

            birthday_str = guest_info.get("birthday")
            if birthday_str and len(birthday_str) >= 10:
                try:
                    from datetime import datetime
                    parsed_birthday = datetime.strptime(birthday_str[:10], '%Y-%m-%d').date()
                    if customer.birthday != parsed_birthday:
                        customer.birthday = parsed_birthday
                        update_fields.append('birthday')
                except Exception as e:
                    logger.error(f"Error parsing birthday '{birthday_str}' for customer {customer.id}: {e}")

            # Update Wallets and Balance
            wallet_balances = guest_info.get("walletBalances", [])
            from apps.loyalty.models import CustomerWallet
            
            synced_wallet_ids = []
            total_active_balance = 0.0
            
            for wallet in wallet_balances:
                w_id = wallet.get("id")
                w_name = wallet.get("name")
                w_type = wallet.get("type", 1)
                w_balance = float(wallet.get("balance", 0))
                
                if w_id:
                    synced_wallet_ids.append(w_id)
                    CustomerWallet.objects.update_or_create(
                        customer=customer,
                        wallet_id=w_id,
                        defaults={
                            'name': w_name or "Кошелек лояльности",
                            'balance': w_balance,
                            'wallet_type': w_type
                        }
                    )
                    if w_type == 1:
                        total_active_balance += w_balance

            # Clean up obsolete wallets
            CustomerWallet.objects.filter(customer=customer).exclude(wallet_id__in=synced_wallet_ids).delete()
            
            if customer.loyalty_balance != total_active_balance:
                customer.loyalty_balance = total_active_balance
                update_fields.append('loyalty_balance')

            # Update Categories
            categories = guest_info.get("categories", [])
            if categories:
                customer.iiko_categories = categories
                update_fields.append('iiko_categories')

            # Update Cards
            cards = guest_info.get("cards", [])
            if cards:
                card = cards[0]
                customer.iiko_card_id = card.get("id")
                customer.iiko_card_number = card.get("number")
                update_fields.extend(['iiko_card_id', 'iiko_card_number'])

            if update_fields:
                customer.save(update_fields=list(set(update_fields)))

    except Exception as exc:
        logger.error(f"Error syncing customer {customer_id} to iiko: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)

@app.task
def sync_all_customers_points():
    logger.info("Starting periodic sync of customer loyalty points...")
    customers = Customer.objects.filter(is_active=True, iiko_customer_id__isnull=False)
    
    org_groups = {}
    for c in customers:
        org_groups.setdefault(c.organization, []).append(c)

    for org, org_customers in org_groups.items():
        try:
            service = IikoLoyaltyService(org)
            for customer in org_customers:
                try:
                    points = service.get_customer_balance(customer.iiko_customer_id)
                    if customer.loyalty_balance != points:
                        customer.loyalty_balance = points
                        customer.save(update_fields=['loyalty_balance'])
                except Exception as e:
                    logger.error(f"Failed to sync points for customer {customer.id}: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize iiko service for organization {org.id}: {e}")

@app.task(bind=True, max_retries=3, default_retry_delay=10)
def register_tg_webhook(self, organization_id):
    from apps.core.models import Organization
    from django.conf import settings
    try:
        org = Organization.objects.get(id=organization_id)
        if not org.tg_bot_token:
            return
        
        webhook_url = f"{settings.WEBHOOK_DOMAIN.rstrip('/')}/api/loyalty/webhook/{org.id}/{org.tg_bot_token}/"
        url = f"https://api.telegram.org/bot{org.tg_bot_token}/setWebhook"
        
        response = requests.post(url, json={"url": webhook_url}, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully registered webhook for organization {organization_id}")
    except Exception as exc:
        logger.error(f"Error registering Telegram Webhook for organization {organization_id}: {exc}")
        raise self.retry(exc=exc)

@app.task
def process_iiko_webhook(log_id):
    from apps.loyalty.models import IikoWebhookLog, Customer
    from apps.core.models import Organization
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    from apps.loyalty.views import send_telegram_message
    from apps.core.utils import normalize_phone

    try:
        log = IikoWebhookLog.objects.get(id=log_id)
        if log.status != 'PENDING':
            return
            
        payload = log.payload
        actual_payload = payload.get('body', payload) if isinstance(payload, dict) else payload
        
        # Deduplication based on transactionId
        transaction_id = actual_payload.get('transactionId')
        if transaction_id:
            from django.core.cache import cache
            from django.db.models import Q
            
            # Check Redis cache lock (atomic SETNX check)
            lock_key = f"iiko_tx_{transaction_id}"
            is_new = cache.add(lock_key, 'processed', timeout=3600)
            
            # Check DB to see if there is already a SUCCESS log with the same transactionId
            already_processed = IikoWebhookLog.objects.filter(
                status='SUCCESS'
            ).filter(
                Q(payload__transactionId=transaction_id) | Q(payload__body__transactionId=transaction_id)
            ).exclude(id=log_id).exists()
            
            if not is_new or already_processed:
                logger.info(f"Deduplicated transactionId: {transaction_id} (cache_is_new={is_new}, db_processed={already_processed})")
                log.status = 'SUCCESS'
                log.error_message = f"Deduplicated transactionId: {transaction_id}"
                log.save()
                return

        org_id_str = actual_payload.get('organizationId')
        uoc_id_str = actual_payload.get('uocId')
        customer_id_str = actual_payload.get('customerId')
        balance = actual_payload.get('balance', 0)
        change_amount = actual_payload.get('sum', 0)
        
        org = None
        for lookup_id in [org_id_str, uoc_id_str]:
            if not lookup_id:
                continue
            org = Organization.objects.filter(iiko_organization_id=lookup_id, is_active=True).first()
            if org:
                break

        if not org:
            log.status = 'FAILED'
            log.error_message = f"Organization not found: organizationId={org_id_str}, uocId={uoc_id_str}"
            log.save()
            return

        if not customer_id_str:
            log.status = 'FAILED'
            log.error_message = "No customerId in payload"
            log.save()
            return

        # Identify if this is a wallet transaction (notificationType == 1, or has both balance and sum)
        notification_type = actual_payload.get('notificationType')
        is_wallet_tx = (notification_type == 1) or ('balance' in actual_payload and 'sum' in actual_payload)

        # Find or create customer
        customer = Customer.objects.filter(organization=org, iiko_customer_id=customer_id_str).first()
        
        if not customer:
            # Maybe search by phone if it exists in payload
            phone = actual_payload.get('phone')
            if phone:
                phone = normalize_phone(phone)
                customer = Customer.objects.filter(organization=org, phone=phone).first()
                
            if not customer:
                customer = Customer.objects.create(
                    organization=org,
                    iiko_customer_id=customer_id_str,
                    phone=phone,
                    loyalty_balance=balance if is_wallet_tx else 0
                )
            else:
                customer.iiko_customer_id = customer_id_str
                customer.save()
        
        if is_wallet_tx:
            # Update specific CustomerWallet or fallback to loyalty_balance
            wallet_id = actual_payload.get('walletId')
            if wallet_id:
                from apps.loyalty.models import CustomerWallet
                wallet, w_created = CustomerWallet.objects.get_or_create(
                    customer=customer,
                    wallet_id=wallet_id,
                    defaults={
                        'name': "Кошелек лояльности",
                        'balance': balance,
                        'wallet_type': 1
                    }
                )
                if not w_created:
                    wallet.balance = balance
                    wallet.save(update_fields=['balance'])
                
                total_active_balance = sum(float(w.balance) for w in customer.wallets.filter(wallet_type=1))
                if customer.loyalty_balance != total_active_balance:
                    customer.loyalty_balance = total_active_balance
                    customer.save(update_fields=['loyalty_balance'])
            else:
                if customer.loyalty_balance != balance:
                    customer.loyalty_balance = balance
                    customer.save(update_fields=['loyalty_balance'])

            # Notify via Websockets if user has active session
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{customer.id}",
                    {
                        "type": "user_update",
                        "message": {
                            "event": "balance_updated",
                            "balance": str(balance)
                        }
                    }
                )
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")

            # Send Telegram Push only if there is a non-zero change
            if change_amount != 0 and customer.telegram_id and org.tg_bot_token:
                if customer.language == 'kz':
                    if change_amount > 0:
                        text = f"🔥 Сізге {org.name} мекемесінде {change_amount} бонус берілді! Ағымдағы балансыңыз: {balance} бонус. Сізді қайта күтеміз! 🥰"
                    else:
                        text = f"💳 Бонустарды шешу: {org.name} мекемесінде {abs(change_amount)} б. Картадағы қалдық: {balance} бонус. Келгеніңізге рақмет! ✨"
                    btn_text = "Картаны ашу"
                else:
                    if change_amount > 0:
                        text = f"🔥 Вам начислено {change_amount} бонусов в заведении {org.name}! Ваш текущий баланс: {balance} бонусов. Ждем вас снова! 🥰"
                    else:
                        text = f"💳 Списание бонусов: {abs(change_amount)} б. в {org.name}. Остаток на карте: {balance} бонусов. Спасибо за визит! ✨"
                    btn_text = "Открыть карту"
                
                tma_link = org.get_tma_link()
                inline_keyboard = [
                    [{"text": btn_text, "url": tma_link}]
                ] if tma_link else None
                
                send_telegram_message(org.tg_bot_token, customer.telegram_id, text, inline_keyboard)
        else:
            # For non-wallet transactions (card changes, category updates, inclusion in program, simple push)
            text = None
            btn_text = "Открыть карту" if customer.language != 'kz' else "Картаны ашу"

            if notification_type == 2 or log.event_type == 'SetGuestCategoryTransaction':
                if customer.language == 'kz':
                    text = f"✨ {org.name} адалдық бағдарламасындағы мәртебеңіз жаңартылды!"
                else:
                    text = f"✨ Ваш статус в программе лояльности {org.name} обновлен!"
            elif notification_type == 3 or log.event_type == 'MagnetCardChanged':
                card_number = actual_payload.get('number')
                if card_number:
                    if customer.iiko_card_number != card_number:
                        customer.iiko_card_number = card_number
                        customer.save(update_fields=['iiko_card_number'])
                    if customer.language == 'kz':
                        text = f"💳 Сізге {org.name} мекемесінде № {card_number} виртуалды адалдық картасы берілді!"
                    else:
                        text = f"💳 Вам выпущена виртуальная карта лояльности № {card_number} в заведении {org.name}!"
            elif notification_type == 4 or log.event_type == 'InclusionInProgram':
                if customer.language == 'kz':
                    text = f"🎉 {org.name} мекемесінің адалдық бағдарламасына қош келдіңіз!"
                else:
                    text = f"🎉 Добро пожаловать в программу лояльности заведения {org.name}!"
            elif notification_type == 5 or log.event_type == 'SimplePush':
                text = actual_payload.get('text')

            if text and customer.telegram_id and org.tg_bot_token:
                tma_link = org.get_tma_link()
                inline_keyboard = [
                    [{"text": btn_text, "url": tma_link}]
                ] if tma_link else None
                send_telegram_message(org.tg_bot_token, customer.telegram_id, text, inline_keyboard)

            # Sync user details (including correct balance, cards, categories) in background
            from apps.loyalty.tasks import sync_customer_to_iiko
            sync_customer_to_iiko.delay(customer.id, push=False)
        
        log.status = 'SUCCESS'
        log.error_message = None
        log.save()
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        try:
            log = IikoWebhookLog.objects.get(id=log_id)
            log.status = 'FAILED'
            log.error_message = str(e)
            log.save()
        except Exception:
            pass
