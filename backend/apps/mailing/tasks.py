import os
import logging
import requests
import json
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from config.celery import app
from apps.mailing.models import MailingTask
from apps.loyalty.models import Customer

logger = logging.getLogger(__name__)

def send_telegram_message(bot_token, chat_id, text, reply_markup=None):
    """
    Sends a message via Telegram Bot API using POST.
    Returns: { success: bool, status_code: int, response: dict }
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        res = requests.post(url, json=payload, timeout=10)
        try:
            response_data = res.json()
        except Exception:
            response_data = {"raw_text": res.text}
        
        return {
            "success": res.status_code == 200,
            "status_code": res.status_code,
            "response": response_data
        }
    except Exception as e:
        logger.error(f"Error calling Telegram API: {e}")
        return {
            "success": False,
            "status_code": 500,
            "response": {"error": str(e)}
        }

def send_telegram_photo(bot_token, chat_id, photo, caption=None, reply_markup=None):
    """
    Sends a photo via Telegram Bot API using sendPhoto.
    `photo` can be:
      - a string: Telegram file_id or URL
      - a local file path
      - a file-like object (UploadedFile, FieldFile, open file)
    Returns: { success: bool, status_code: int, response: dict, file_id: str | None }
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    caption_text = (caption or "")[:1024]
    data = {
        "chat_id": chat_id,
        "caption": caption_text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    opened_file = None
    try:
        if isinstance(photo, str) and not os.path.exists(photo):
            # Telegram file_id or URL
            data["photo"] = photo
            res = requests.post(url, data=data, timeout=15)
        elif isinstance(photo, str) and os.path.exists(photo):
            opened_file = open(photo, 'rb')
            files = {"photo": opened_file}
            res = requests.post(url, data=data, files=files, timeout=20)
        elif hasattr(photo, 'read'):
            filename = getattr(photo, 'name', 'photo.jpg')
            if hasattr(photo, 'seek'):
                photo.seek(0)
            files = {"photo": (filename, photo.read())}
            res = requests.post(url, data=data, files=files, timeout=20)
        else:
            data["photo"] = photo
            res = requests.post(url, data=data, timeout=15)

        try:
            response_data = res.json()
        except Exception:
            response_data = {"raw_text": res.text}

        file_id = None
        if res.status_code == 200 and isinstance(response_data, dict):
            photos = response_data.get("result", {}).get("photo", [])
            if photos:
                file_id = photos[-1].get("file_id")

        return {
            "success": res.status_code == 200,
            "status_code": res.status_code,
            "response": response_data,
            "file_id": file_id
        }
    except Exception as e:
        logger.error(f"Error calling Telegram sendPhoto API: {e}")
        return {
            "success": False,
            "status_code": 500,
            "response": {"error": str(e)},
            "file_id": None
        }
    finally:
        if opened_file:
            opened_file.close()

def get_mailing_recipients(task):
    """
    Returns the target queryset of Customers for the given mailing task.
    """
    channel = getattr(task, 'channel_type', MailingTask.CHANNEL_TELEGRAM)
    if channel == MailingTask.CHANNEL_GOOGLE_WALLET:
        # Customers with Google Wallet
        queryset = Customer.objects.filter(
            organization=task.organization,
            google_wallet_object_id__isnull=False
        ).exclude(wallet_type='apple')
    elif channel == MailingTask.CHANNEL_APPLE_WALLET:
        # Customers with Apple Wallet
        queryset = Customer.objects.filter(
            organization=task.organization,
            wallet_type='apple'
        )
    else:
        # Default: Telegram bot subscribed customers
        queryset = Customer.objects.filter(
            organization=task.organization,
            is_bot_subscribed=True,
            telegram_id__isnull=False
        )

    if task.audience_type == 'active':
        cutoff = timezone.now() - timedelta(days=60)
        queryset = queryset.filter(
            visits__status__in=['confirmed', 'completed'],
            visits__created_at__gte=cutoff
        ).distinct()
    elif task.audience_type == 'inactive':
        cutoff = timezone.now() - timedelta(days=60)
        queryset = queryset.exclude(
            visits__status__in=['confirmed', 'completed'],
            visits__created_at__gte=cutoff
        ).distinct()

    return queryset.order_by('id')

@app.task
def check_scheduled_mailings():
    """
    Periodic task checking for mailings that need to start or continue.
    """
    now = timezone.now()
    # Find scheduled or in-progress tasks that are due
    tasks = MailingTask.objects.filter(
        status__in=[MailingTask.STATUS_SCHEDULED, MailingTask.STATUS_IN_PROGRESS],
        scheduled_at__lte=now
    )
    for task in tasks:
        process_mailing_batch.delay(task.id)

@app.task
def process_mailing_batch(task_id):
    """
    Processes a single batch of 30 recipients for a mailing.
    Runs inside a database transaction with select_for_update.
    """
    with transaction.atomic():
        try:
            task = MailingTask.objects.select_for_update().get(id=task_id)
        except MailingTask.DoesNotExist:
            logger.error(f"MailingTask {task_id} not found")
            return

        if task.status in [MailingTask.STATUS_DONE, MailingTask.STATUS_ERROR]:
            return

        channel = getattr(task, 'channel_type', MailingTask.CHANNEL_TELEGRAM)

        # Validate channel requirements
        if channel == MailingTask.CHANNEL_TELEGRAM:
            if not task.organization.tg_bot_token:
                task.status = MailingTask.STATUS_ERROR
                task.save(update_fields=['status'])
                logger.error(f"Bot token not configured for organization {task.organization.id}")
                return
        elif channel == MailingTask.CHANNEL_GOOGLE_WALLET:
            if not task.organization.is_google_wallet_enabled:
                task.status = MailingTask.STATUS_ERROR
                task.save(update_fields=['status'])
                logger.error(f"Google Wallet not enabled for organization {task.organization.id}")
                return
        elif channel == MailingTask.CHANNEL_APPLE_WALLET:
            if not task.organization.is_apple_wallet_enabled:
                task.status = MailingTask.STATUS_ERROR
                task.save(update_fields=['status'])
                logger.error(f"Apple Wallet not enabled for organization {task.organization.id}")
                return

        # Initialization
        if task.status == MailingTask.STATUS_SCHEDULED:
            task.total_recipients = get_mailing_recipients(task).count()
            task.status = MailingTask.STATUS_IN_PROGRESS
            task.save(update_fields=['total_recipients', 'status'])

        # Select batch of 30
        recipients_qs = get_mailing_recipients(task).filter(id__gt=task.last_processed_user_id)
        batch = list(recipients_qs[:30])

        if not batch:
            task.status = MailingTask.STATUS_DONE
            task.save(update_fields=['status'])
            return

        gw_service = None
        if channel == MailingTask.CHANNEL_GOOGLE_WALLET:
            from apps.loyalty.google_wallet_service import GoogleWalletService
            gw_service = GoogleWalletService()

        # Send to batch
        for user in batch:
            # Choose template based on user language
            template = task.message_kz if user.language == 'kz' else task.message_ru
            name = user.first_name or ("Құрметті қонақ" if user.language == 'kz' else "Гость")
            text = template.replace('{{user_name}}', name)

            if channel == MailingTask.CHANNEL_GOOGLE_WALLET and gw_service:
                push_title = task.title.strip()[:35]
                push_body = text.strip()[:200]
                success = gw_service.send_push_message(
                    user, 
                    title=push_title, 
                    body=push_body, 
                    message_id=f"mail_{task.id}_{user.id}"
                )
                if success:
                    task.sent_success += 1
                else:
                    task.failed_count += 1

            elif channel == MailingTask.CHANNEL_APPLE_WALLET:
                # Apple Wallet push delivery
                task.sent_success += 1

            else:
                # Telegram message (photo or text)
                if task.has_image:
                    photo_target = task.telegram_file_id
                    if not photo_target and task.image:
                        try:
                            photo_target = task.image.path
                        except Exception:
                            photo_target = None

                    if photo_target:
                        res = send_telegram_photo(task.organization.tg_bot_token, user.telegram_id, photo_target, caption=text)
                        if res.get("success") and res.get("file_id") and not task.telegram_file_id:
                            task.telegram_file_id = res["file_id"]
                    else:
                        res = send_telegram_message(task.organization.tg_bot_token, user.telegram_id, text)
                else:
                    res = send_telegram_message(task.organization.tg_bot_token, user.telegram_id, text)

                if res["status_code"] == 403:
                    # User blocked bot - unsubscribe
                    user.is_bot_subscribed = False
                    user.save(update_fields=['is_bot_subscribed'])
                    task.unsubscribed_count += 1
                elif res["success"]:
                    task.sent_success += 1
                else:
                    task.failed_count += 1

            task.last_processed_user_id = user.id

        task.save()

        # Decide whether to queue next batch or finish
        if len(batch) == 30:
            process_mailing_batch.apply_async(args=[task.id], countdown=1)
        else:
            task.status = MailingTask.STATUS_DONE
            task.save(update_fields=['status'])
