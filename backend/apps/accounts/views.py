import requests
import json
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from apps.accounts.models import UserOrganization
from apps.accounts.serializers import (
    CustomTokenObtainPairSerializer, EmployeeSerializer, EmployeeCreateSerializer, SuperAdminUserSerializer
)
from apps.accounts.permissions import IsOrgManager, IsSuperAdmin
from apps.core.models import Organization
from apps.loyalty.models import Customer
from apps.core.utils import normalize_phone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()

class EmployeeTokenView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class EmployeeViewSet(viewsets.ViewSet):
    """
    ViewSet for OrgManager to manage employees of their organization.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrgManager]

    def list(self, request, organization_id=None):
        employees = User.objects.filter(memberships__organization_id=organization_id).distinct()
        serializer = EmployeeSerializer(employees, many=True, context={'organization_id': organization_id})
        return Response(serializer.data)

    def create(self, request, organization_id=None):
        serializer = EmployeeCreateSerializer(data=request.data, context={'organization_id': organization_id})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Serialize the created employee details
        employee_data = EmployeeSerializer(user, context={'organization_id': organization_id}).data
        return Response(employee_data, status=status.HTTP_201_CREATED)

    def destroy(self, request, organization_id=None, pk=None):
        membership = get_object_or_404(UserOrganization, organization_id=organization_id, user_id=pk)
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SuperAdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SuperAdmin to manage organization managers.
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = SuperAdminUserSerializer
    queryset = User.objects.filter(
        is_superuser=False,
        memberships__role=UserOrganization.ROLE_ORG_MANAGER
    ).distinct().order_by('-id')


def send_tg_message_inline(bot_token, chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        res = requests.post(url, json=payload, timeout=5)
        res.raise_for_status()
    except Exception:
        pass

def answer_callback_query(bot_token, callback_query_id, text=None):
    url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
    payload = {
        "callback_query_id": callback_query_id
    }
    if text:
        payload["text"] = text
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

class TmaWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, org_slug, token, *args, **kwargs):
        org = get_object_or_404(Organization, slug=org_slug, is_active=True)
        if org.tg_bot_token != token:
            return Response({"error": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        
        # 1. Handle Callback Query (Consent collection)
        callback_query = data.get('callback_query')
        if callback_query:
            callback_data = callback_query.get('data', '')
            callback_id = callback_query.get('id')
            from_user = callback_query.get('from', {})
            chat_id = from_user.get('id')
            
            if callback_data.startswith('consent_') and chat_id:
                parts = callback_data.split('_')
                if len(parts) == 3:
                    action = parts[1] # 'yes' or 'no'
                    user_id = parts[2] # customer database ID
                    
                    try:
                        customer = Customer.objects.get(id=user_id, organization=org)
                        if action == 'yes':
                            customer.is_bot_subscribed = True
                            reply_text = "Благодарим за доверие!"
                        else:
                            customer.is_bot_subscribed = False
                            reply_text = "Хорошо, мы не будем беспокоить вас рассылками."
                        customer.save(update_fields=['is_bot_subscribed'])
                        
                        # Send telegram response with inline keyboard to return to TMA
                        tma_link = org.get_tma_link()
                        inline_keyboard = [
                            [{"text": "Вернуться в приложение", "url": tma_link}]
                        ] if tma_link else None
                        reply_markup = {"inline_keyboard": inline_keyboard} if inline_keyboard else None
                        
                        send_tg_message_inline(org.tg_bot_token, chat_id, reply_text, reply_markup)
                        answer_callback_query(org.tg_bot_token, callback_id)
                        return Response({"status": "success"}, status=status.HTTP_200_OK)
                    except Customer.DoesNotExist:
                        answer_callback_query(org.tg_bot_token, callback_id, "Пользователь не найден")
                        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        # 2. Handle standard message
        message = data.get('message')
        if not message:
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '').strip()

        # Handle /getmyid
        if text == '/getmyid' and chat_id:
            reply_text = f"Ваш Telegram ID: <code>{chat_id}</code>"
            send_tg_message_inline(org.tg_bot_token, chat_id, reply_text)
            return Response({"status": "success"}, status=status.HTTP_200_OK)

        # 3. Handle contact sharing (from original TmaWebhookView in apps.loyalty)
        contact = message.get('contact')
        if contact:
            tg_user_id = contact.get('user_id')
            phone_number = contact.get('phone_number')

            if not tg_user_id or not phone_number:
                return Response({"error": "Invalid contact data"}, status=status.HTTP_400_BAD_REQUEST)

            normalized_phone = normalize_phone(phone_number)

            try:
                customer = Customer.objects.get(organization=org, telegram_id=tg_user_id)
            except Customer.DoesNotExist:
                customer = Customer.objects.create(
                    organization=org,
                    telegram_id=tg_user_id,
                    phone=normalized_phone
                )

            existing_iiko_customer = Customer.objects.filter(
                organization=org, 
                phone=normalized_phone, 
                telegram_id__isnull=True
            ).first()

            if existing_iiko_customer:
                customer.iiko_customer_id = existing_iiko_customer.iiko_customer_id
                customer.iiko_card_number = existing_iiko_customer.iiko_card_number
                customer.iiko_card_id = existing_iiko_customer.iiko_card_id
                customer.iiko_categories = existing_iiko_customer.iiko_categories
                customer.loyalty_balance = existing_iiko_customer.loyalty_balance
                if existing_iiko_customer.wallet_barcode:
                    customer.wallet_barcode = existing_iiko_customer.wallet_barcode
                
                if existing_iiko_customer.first_name:
                    customer.first_name = existing_iiko_customer.first_name
                if existing_iiko_customer.last_name:
                    customer.last_name = existing_iiko_customer.last_name
                if existing_iiko_customer.email:
                    customer.email = existing_iiko_customer.email
                if existing_iiko_customer.birthday:
                    customer.birthday = existing_iiko_customer.birthday

                existing_iiko_customer.delete()

            customer.phone = normalized_phone
            customer.save()

            from apps.loyalty.tasks import sync_customer_to_iiko
            sync_customer_to_iiko.delay(customer.id, push=False)

            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{customer.id}",
                    {
                        "type": "user_update",
                        "message": {
                            "event": "phone_updated",
                            "phone": normalized_phone
                        }
                    }
                )
            except Exception:
                pass

            tma_link = org.get_tma_link()
            if customer.language == 'kz':
                reply_text = "Рақмет! Телефон нөміріңіз сәтті расталды. Енді адалдық бағдарламасына орала аласыз."
                btn_text = "Mini App ашу"
            else:
                reply_text = "Спасибо! Ваш номер телефона успешно подтвержден. Теперь вы можете вернуться в приложение лояльности."
                btn_text = "Открыть Mini App"

            inline_keyboard = [
                [{"text": btn_text, "url": tma_link}]
            ] if tma_link else None

            send_tg_message_inline(org.tg_bot_token, tg_user_id, reply_text, {"inline_keyboard": inline_keyboard} if inline_keyboard else None)
            return Response({"status": "success"}, status=status.HTTP_200_OK)

        return Response({"status": "ignored"}, status=status.HTTP_200_OK)

class SetWebhookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        org_id = request.data.get('organization_id')
        if not org_id:
            return Response({"error": "organization_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify access
        if not request.user.is_superuser:
            membership = request.user.memberships.filter(organization_id=org_id, role__in=[UserOrganization.ROLE_ORG_MANAGER, UserOrganization.ROLE_ORG_ADMIN]).first()
            if not membership:
                return Response({"error": "Permission denied for this organization"}, status=status.HTTP_403_FORBIDDEN)
            org = membership.organization
        else:
            org = get_object_or_404(Organization, id=org_id)

        if not org.tg_bot_token:
            return Response({"error": "Bot token not configured for this organization"}, status=status.HTTP_400_BAD_REQUEST)

        from django.conf import settings
        webhook_url = f"{settings.WEBHOOK_DOMAIN.rstrip('/')}/api/accounts/tma/webhook/{org.slug}/{org.tg_bot_token}/"
        url = f"https://api.telegram.org/bot{org.tg_bot_token}/setWebhook"

        try:
            res = requests.post(url, json={"url": webhook_url}, timeout=10)
            res.raise_for_status()
            data = res.json()
            if not data.get('ok'):
                return Response({"error": data.get('description', 'Unknown error')}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"status": "Webhook successfully registered", "webhook_url": webhook_url})
        except Exception as e:
            return Response({"error": f"Failed to register webhook: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
