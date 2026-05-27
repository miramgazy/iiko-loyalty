import os
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from apps.core.models import Organization
from apps.core.serializers import SuperAdminOrganizationSerializer, OrganizationSettingsSerializer
from apps.accounts.permissions import IsSuperAdmin, IsOrgManager
from apps.loyalty.google_wallet_service import GoogleWalletService
from apps.accounts.permissions import IsSuperAdmin, IsOrgManager

class SuperAdminOrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for global SaaS admin to manage restaurant organizations.
    """
    queryset = Organization.objects.all().order_by('-created_at')
    serializer_class = SuperAdminOrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        # Allow toggling activation or updating details
        partial = kwargs.pop('partial', False)
        instance = self.get_object_or_404_by_pk(kwargs.get('pk'))
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def get_object_or_404_by_pk(self, pk):
        return get_object_or_404(Organization, pk=pk)

class OrganizationSettingsView(APIView):
    """
    View for OrgManager to view and modify their organization's settings.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrgManager]

    def get(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        serializer = OrganizationSettingsSerializer(org)
        return Response(serializer.data)

    def patch(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        serializer = OrganizationSettingsSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Trigger webhook registration if bot token is updated
        if 'tg_bot_token' in request.data:
            from apps.loyalty.tasks import register_tg_webhook
            register_tg_webhook.delay(org.id)
            
        return Response(serializer.data)

class OrganizationLogoUploadView(APIView):
    """
    View for OrgManager to upload organization logo image.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrgManager]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        logo_file = request.FILES.get('logo')
        if not logo_file:
            return Response({"error": "No logo file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Basic extension check
        ext = os.path.splitext(logo_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            return Response({"error": "Invalid image format"}, status=status.HTTP_400_BAD_REQUEST)

        # Save to media/logos/
        filename = f"logos/logo_{org.slug}{ext}"
        path = default_storage.save(filename, ContentFile(logo_file.read()))
        
        # Build URL
        logo_url = f"/media/{path}"
        
        # Update organization branding config
        branding = org.branding or {}
        branding['logo_url'] = logo_url
        org.branding = branding
        org.save(update_fields=['branding'])

        return Response({
            "status": "success",
            "logo_url": logo_url
        }, status=status.HTTP_200_OK)

class OrganizationGoogleWalletSettingsView(APIView):
    """
    View for OrgManager to setup Google Wallet class.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrgManager]

    def post(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        
        # Save issuer ID if provided
        issuer_id = request.data.get('issuer_id')
        if issuer_id:
            org.google_issuer_id = issuer_id
            org.save(update_fields=['google_issuer_id'])
            
        if not org.google_issuer_id:
            return Response({"error": "Google Issuer ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = GoogleWalletService()
            result = service.create_or_update_loyalty_class(org, request.data)
            return Response({
                "status": "success",
                "class_id": org.google_loyalty_class_id,
                "google_response": result
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OrganizationWebhookStatusView(APIView):
    """
    View for OrgManager to check Telegram Webhook status.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrgManager]

    def get(self, request, organization_id, *args, **kwargs):
        import requests
        from django.conf import settings
        
        org = get_object_or_404(Organization, id=organization_id)
        if not org.tg_bot_token:
            return Response({"error": "Bot token not configured"}, status=status.HTTP_400_BAD_REQUEST)

        expected_url = f"{settings.WEBHOOK_DOMAIN.rstrip('/')}/api/accounts/tma/webhook/{org.slug}/{org.tg_bot_token}/"
        url = f"https://api.telegram.org/bot{org.tg_bot_token}/getWebhookInfo"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data.get('ok'):
                return Response({"error": data.get('description', 'Unknown error')}, status=status.HTTP_400_BAD_REQUEST)
                
            webhook_info = data.get('result', {})
            return Response({
                "expected_url": expected_url,
                "telegram_response": webhook_info
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, organization_id, *args, **kwargs):
        import requests
        from django.conf import settings
        
        org = get_object_or_404(Organization, id=organization_id)
        if not org.tg_bot_token:
            return Response({"error": "Bot token not configured"}, status=status.HTTP_400_BAD_REQUEST)
            
        webhook_url = f"{settings.WEBHOOK_DOMAIN.rstrip('/')}/api/accounts/tma/webhook/{org.slug}/{org.tg_bot_token}/"
        url = f"https://api.telegram.org/bot{org.tg_bot_token}/setWebhook"
        
        try:
            response = requests.post(url, json={"url": webhook_url}, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data.get('ok'):
                return Response({"error": data.get('description', 'Unknown error')}, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({"status": "Webhook successfully registered", "expected_url": webhook_url})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OrganizationSendTestMessageView(APIView):
    """
    View for OrgManager to send a test message to verify Bot Token from Organization Settings.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrgManager]

    def post(self, request, organization_id, *args, **kwargs):
        import requests
        org = get_object_or_404(Organization, id=organization_id)
        if not org.tg_bot_token:
            return Response({"error": "Бот не настроен для данной организации"}, status=status.HTTP_400_BAD_REQUEST)
            
        telegram_id = request.data.get('telegram_id')
        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        url = f"https://api.telegram.org/bot{org.tg_bot_token}/sendMessage"
        text = f"<b>[ТЕСТ]</b>\nБот заведения <b>{org.name}</b> успешно настроен и подключен!"
        
        try:
            response = requests.post(url, json={
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": "HTML"
            }, timeout=10)
            data = response.json()
            if not data.get('ok'):
                return Response({"error": data.get('description', 'Unknown error')}, status=status.HTTP_400_BAD_REQUEST)
                
            # Auto-save admin's telegram_id to their profile if it changed/was blank
            if request.user.telegram_id != telegram_id:
                request.user.telegram_id = telegram_id
                request.user.save(update_fields=['telegram_id'])
                
            return Response({"status": "success", "detail": "Test message sent successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
