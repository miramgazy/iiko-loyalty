import json
import requests
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import Organization
from apps.core.utils import normalize_phone
from apps.loyalty.models import Customer, IikoWebhookLog, LoyaltyProgram
from apps.loyalty.serializers import CustomerSerializer, LoyaltyProgramSerializer
from apps.loyalty.views_utils import validate_tg_init_data, get_tokens_for_customer
from apps.accounts.permissions import IsOrgEmployee
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class TmaAuthView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


    def post(self, request, *args, **kwargs):
        init_data = request.data.get('initData')
        bot_username = request.data.get('bot_username')

        if not init_data:
            return Response(
                {"error": "initData is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        org = None
        user_data = None
        
        # 1. Try finding org by bot_username if provided
        if bot_username:
            if bot_username.startswith('@'):
                bot_username = bot_username[1:]
            try:
                org = Organization.objects.get(tg_bot_username=bot_username, is_active=True)
                user_data = validate_tg_init_data(init_data, org.tg_bot_token)
            except (Organization.DoesNotExist, ValueError):
                org = None
                user_data = None

        # 2. Fallback: try all active organizations to find matching signature
        if not org or not user_data:
            for active_org in Organization.objects.filter(is_active=True):
                if active_org.tg_bot_token:
                    try:
                        user_data = validate_tg_init_data(init_data, active_org.tg_bot_token)
                        org = active_org
                        break
                    except ValueError:
                        continue

        if not org or not user_data:
            return Response(
                {"error": "Could not validate Telegram signature or find matching organization"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 3. Find or create Customer
        telegram_id = user_data.get('id')
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')

        customer, created = Customer.objects.get_or_create(
            organization=org,
            telegram_id=telegram_id,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        if not created and (customer.first_name != first_name or customer.last_name != last_name):
            if not customer.is_onboarded:
                customer.first_name = first_name
                customer.last_name = last_name
                customer.save()

        # 4. Generate JWT tokens
        tokens = get_tokens_for_customer(customer)

        return Response({
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "organization": {
                "id": org.id,
                "slug": org.slug,
                "name": org.name,
                "branding": org.branding,
                "instagram_link": org.instagram_link,
                "whatsapp_link": org.whatsapp_link
            },
            "customer": CustomerSerializer(customer).data
        }, status=status.HTTP_200_OK)

class CustomerMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not isinstance(request.user, Customer):
            return Response({"error": "Unauthorized, not a Customer"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CustomerSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        if not isinstance(request.user, Customer):
            return Response({"error": "Unauthorized, not a Customer"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CustomerSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            customer = serializer.save()
            from apps.loyalty.tasks import sync_customer_to_iiko
            sync_customer_to_iiko.delay(customer.id, push=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not isinstance(request.user, Customer):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
        from apps.loyalty.tasks import sync_customer_to_iiko
        try:
            # Вызываем функцию напрямую для синхронного выполнения
            sync_customer_to_iiko(request.user.id, push=False)
            # Обновляем объект из БД
            request.user.refresh_from_db()
            serializer = CustomerSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TmaWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


    def post(self, request, org_id, bot_token, *args, **kwargs):
        org = get_object_or_404(Organization, id=org_id, is_active=True)
        if org.tg_bot_token != bot_token:
            return Response({"error": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        message = data.get('message')
        if not message:
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        contact = message.get('contact')
        if not contact:
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        tg_user_id = contact.get('user_id')
        phone_number = contact.get('phone_number')

        if not tg_user_id or not phone_number:
            return Response({"error": "Invalid contact data"}, status=status.HTTP_400_BAD_REQUEST)

        normalized_phone = normalize_phone(phone_number)

        try:
            customer = Customer.objects.get(organization=org, telegram_id=tg_user_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

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
            
            # Copy profile details from existing iiko customer if they exist
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
            text = "Рақмет! Телефон нөміріңіз сәтті расталды. Енді адалдық бағдарламасына орала аласыз."
            btn_text = "Mini App ашу"
        else:
            text = "Спасибо! Ваш номер телефона успешно подтвержден. Теперь вы можете вернуться в приложение лояльности."
            btn_text = "Открыть Mini App"

        inline_keyboard = [
            [{"text": btn_text, "url": tma_link}]
        ] if tma_link else None

        send_telegram_message(org.tg_bot_token, tg_user_id, text, inline_keyboard)

        return Response({"status": "success"}, status=status.HTTP_200_OK)

def send_telegram_message(bot_token, chat_id, text, inline_keyboard=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if inline_keyboard:
        payload["reply_markup"] = json.dumps({"inline_keyboard": inline_keyboard})
    try:
        res = requests.post(url, json=payload, timeout=5)
        res.raise_for_status()
    except Exception:
        pass

class OrgCustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for OrgManager/OrgAdmin to view and search customers of their organization.
    """
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get_queryset(self):
        org_id = self.kwargs.get('organization_id')
        queryset = Customer.objects.filter(organization_id=org_id).order_by('-created_at')
        
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset

from apps.loyalty.google_wallet_service import GoogleWalletService

class CustomerGoogleWalletLinkView(APIView):
    """
    View for generating Google Wallet Save URL for the current Customer.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        customer = request.user
        if not isinstance(customer, Customer):
            return Response({"error": "Unauthorized, not a Customer"}, status=status.HTTP_403_FORBIDDEN)
            
        if not customer.is_onboarded:
            return Response({"error": "Вам необходимо подтвердить номер телефона"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            service = GoogleWalletService()
            balance_str = str(int(customer.loyalty_balance)) if customer.loyalty_balance == int(customer.loyalty_balance) else str(customer.loyalty_balance)
            url = service.generate_google_wallet_link(customer, f"{balance_str} баллов")
            return Response({"url": url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class IikoWebhookView(APIView):
    """
    Webhook receiver for iiko Cloud events.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


    def post(self, request, *args, **kwargs):
        data = request.data
        if not data:
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        payloads = data if isinstance(data, list) else [data]

        for payload in payloads:
            actual_payload = payload.get('body', payload) if isinstance(payload, dict) else payload
            
            # Extract organization ID and uoc ID
            org_id_str = None
            uoc_id_str = None
            if isinstance(actual_payload, dict):
                org_id_str = actual_payload.get('organizationId')
                uoc_id_str = actual_payload.get('uocId')

            # Create log right away to capture the request
            log = IikoWebhookLog.objects.create(
                organization_id=org_id_str or uoc_id_str or None,
                event_type=actual_payload.get('transactionType', 'Unknown') if isinstance(actual_payload, dict) else 'Unknown',
                payload=payload,
                status='FAILED'
            )

            if not isinstance(actual_payload, dict):
                log.error_message = "Payload body is not a JSON object"
                log.save()
                continue

            # Check execution mode (test events from iiko)
            execution_mode = None
            if isinstance(payload, dict):
                execution_mode = payload.get('executionMode')
            if not execution_mode and isinstance(actual_payload, dict):
                execution_mode = actual_payload.get('executionMode')

            if execution_mode == 'test':
                log.status = 'SUCCESS'
                log.error_message = "Test execution mode. Ignored."
                log.save()
                continue

            if not org_id_str and not uoc_id_str:
                log.error_message = "Missing organizationId and uocId in payload"
                log.save()
                continue

            # Try to lookup organization by organizationId first, then uocId
            org = None
            for lookup_id in [org_id_str, uoc_id_str]:
                if not lookup_id:
                    continue
                try:
                    org = Organization.objects.get(iiko_organization_id=lookup_id, is_active=True)
                    break
                except Exception:
                    continue

            if not org:
                log.error_message = f"Organization not found for organizationId: '{org_id_str}' or uocId: '{uoc_id_str}'"
                log.save()
                continue

            if org.is_iiko_webhook_password_enabled:
                expected_password = org.iiko_webhook_password or ""
                provided_password = actual_payload.get('subscriptionPassword', "")
                if provided_password != expected_password:
                    log.error_message = "Invalid subscription password"
                    log.save()
                    return Response({"error": "Invalid subscription password"}, status=status.HTTP_403_FORBIDDEN)
            
            # If all checks pass, set status to PENDING and process
            log.status = 'PENDING'
            log.error_message = None
            log.save()
            
            from apps.loyalty.tasks import process_iiko_webhook
            process_iiko_webhook.delay(log.id)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

class LoyaltyProgramViewSet(viewsets.ModelViewSet):
    serializer_class = LoyaltyProgramSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOrgEmployee()]

    def get_queryset(self):
        org_id = self.kwargs.get('organization_id')
        return LoyaltyProgram.objects.filter(organization_id=org_id).order_by('-created_at')

    def perform_create(self, serializer):
        org_id = self.kwargs.get('organization_id')
        org = get_object_or_404(Organization, id=org_id)
        serializer.save(organization=org)
