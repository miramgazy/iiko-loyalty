from rest_framework import viewsets, permissions, status, serializers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.mailing.models import MailingTask
from apps.mailing.serializers import MailingTaskSerializer
from apps.core.models import Organization
from apps.accounts.permissions import IsOrgEmployee

def get_user_org(request):
    org_id = request.query_params.get('organization_id') or request.data.get('organization_id')
    if org_id:
        if request.user.is_superuser:
            return get_object_or_404(Organization, id=org_id)
        membership = request.user.memberships.filter(organization_id=org_id).first()
        if membership:
            return membership.organization
    if request.user.is_superuser:
        return Organization.objects.first()
    membership = request.user.memberships.first()
    return membership.organization if membership else None

class MailingTaskViewSet(viewsets.ModelViewSet):
    serializer_class = MailingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return MailingTask.objects.all()
        
        # Limit to organizations where user has membership
        org_ids = self.request.user.memberships.values_list('organization_id', flat=True)
        org_id = self.request.query_params.get('organization_id')
        
        if org_id:
            return MailingTask.objects.filter(organization_id=org_id, organization_id__in=org_ids)
        return MailingTask.objects.filter(organization_id__in=org_ids)

    def perform_create(self, serializer):
        org = get_user_org(self.request)
        if not org:
            raise serializers.ValidationError("Organization not found or permission denied.")
        
        # When creating, status defaults to scheduled
        serializer.save(organization=org, status=MailingTask.STATUS_SCHEDULED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Deletion is only allowed for draft or scheduled tasks
        if instance.status not in [MailingTask.STATUS_DRAFT, MailingTask.STATUS_SCHEDULED]:
            return Response(
                {"error": "Рассылку можно удалить только в статусе Черновик или Запланирована"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def count_recipients(self, request):
        audience_type = request.query_params.get('audience_type', 'all')
        channel_type = request.query_params.get('channel_type', MailingTask.CHANNEL_TELEGRAM)
        org = get_user_org(request)
        if not org:
            return Response({"error": "Organization context not found"}, status=status.HTTP_400_BAD_REQUEST)

        # Build dummy task to query recipients
        mock_task = MailingTask(organization=org, audience_type=audience_type, channel_type=channel_type)
        from apps.mailing.tasks import get_mailing_recipients
        count = get_mailing_recipients(mock_task).count()
        return Response({"count": count})

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def get_file_id(self, request):
        image = request.FILES.get('image')
        tg_id_for_test = request.data.get('tg_id_for_test') or request.data.get('telegram_id')
        message_ru = request.data.get('message_ru', '')
        message_kz = request.data.get('message_kz', '')

        if not tg_id_for_test:
            return Response({"error": "Укажите Telegram ID для теста"}, status=status.HTTP_400_BAD_REQUEST)

        if not image:
            return Response({"error": "Загрузите изображение для получения File ID"}, status=status.HTTP_400_BAD_REQUEST)

        org = get_user_org(request)
        if not org:
            return Response({"error": "Organization context not found"}, status=status.HTTP_400_BAD_REQUEST)

        if not org.tg_bot_token:
            return Response({"error": "Бот не настроен для данной организации"}, status=status.HTTP_400_BAD_REQUEST)

        # Select template by admin user language
        admin_lang = getattr(request.user, 'language', 'ru')
        template = message_kz if admin_lang == 'kz' else message_ru

        # Format name
        admin_name = request.user.first_name or request.user.username or "Администратор"
        text = template.replace('{{user_name}}', admin_name) if template else "Тестовое изображение"
        test_caption = f"<b>[ТЕСТОВОЕ ФОТО]</b>\n\n{text}"

        from apps.mailing.tasks import send_telegram_photo
        res = send_telegram_photo(org.tg_bot_token, tg_id_for_test, image, caption=test_caption)

        if res["success"]:
            file_id = res.get("file_id")
            if not file_id:
                photos = res.get("response", {}).get("result", {}).get("photo", [])
                if photos:
                    file_id = photos[-1].get("file_id")

            # Auto-save admin's telegram_id to their profile if it changed/was blank
            if request.user.telegram_id != tg_id_for_test:
                request.user.telegram_id = tg_id_for_test
                request.user.save(update_fields=['telegram_id'])

            return Response({
                "status": "success",
                "file_id": file_id,
                "detail": "Тестовое фото отправлено, File ID получен!"
            })
        else:
            return Response(
                {"error": "Не удалось отправить тестовое фото через Telegram API", "detail": res.get("response")},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        task = self.get_object()
        telegram_id = request.data.get('telegram_id') or task.tg_id_for_test
        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        org = task.organization
        if not org.tg_bot_token:
            return Response({"error": "Бот не настроен для данной организации"}, status=status.HTTP_400_BAD_REQUEST)

        # Select template by admin user language
        admin_lang = getattr(request.user, 'language', 'ru')
        template = task.message_kz if admin_lang == 'kz' else task.message_ru

        # Format name
        admin_name = request.user.first_name or request.user.username or "Администратор"
        text = template.replace('{{user_name}}', admin_name)
        test_text = f"<b>[ТЕСТОВОЕ СООБЩЕНИЕ]</b>\n\n{text}"

        if task.has_image:
            photo_target = task.telegram_file_id or (task.image.path if task.image else None)
            from apps.mailing.tasks import send_telegram_photo
            res = send_telegram_photo(org.tg_bot_token, telegram_id, photo_target, test_text)
            if res.get("success") and res.get("file_id") and not task.telegram_file_id:
                task.telegram_file_id = res["file_id"]
                task.save(update_fields=['telegram_file_id'])
        else:
            from apps.mailing.tasks import send_telegram_message
            res = send_telegram_message(org.tg_bot_token, telegram_id, test_text)

        if res["success"]:
            # Auto-save admin's telegram_id to their profile if it changed/was blank
            if request.user.telegram_id != telegram_id:
                request.user.telegram_id = telegram_id
                request.user.save(update_fields=['telegram_id'])
            return Response({"status": "success", "detail": "Test message sent", "file_id": res.get("file_id")})
        else:
            return Response(
                {"error": "Не удалось отправить сообщение через Telegram API", "detail": res.get("response")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def send_test_preview(self, request):
        telegram_id = request.data.get('telegram_id') or request.data.get('tg_id_for_test')
        message_ru = request.data.get('message_ru', '')
        message_kz = request.data.get('message_kz', '')
        has_image = str(request.data.get('has_image', '')).lower() in ['true', '1']
        image = request.FILES.get('image')
        telegram_file_id = request.data.get('telegram_file_id')

        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        org = get_user_org(request)
        if not org:
            return Response({"error": "Organization context not found"}, status=status.HTTP_400_BAD_REQUEST)

        if not org.tg_bot_token:
            return Response({"error": "Бот не настроен для данной организации"}, status=status.HTTP_400_BAD_REQUEST)

        # Select template by admin user language
        admin_lang = getattr(request.user, 'language', 'ru')
        template = message_kz if admin_lang == 'kz' else message_ru

        # Format name
        admin_name = request.user.first_name or request.user.username or "Администратор"
        text = template.replace('{{user_name}}', admin_name)
        test_text = f"<b>[ТЕСТОВОЕ СООБЩЕНИЕ]</b>\n\n{text}"

        if has_image and (telegram_file_id or image):
            photo_target = telegram_file_id if telegram_file_id else image
            from apps.mailing.tasks import send_telegram_photo
            res = send_telegram_photo(org.tg_bot_token, telegram_id, photo_target, test_text)
        else:
            from apps.mailing.tasks import send_telegram_message
            res = send_telegram_message(org.tg_bot_token, telegram_id, test_text)

        if res["success"]:
            # Auto-save admin's telegram_id to their profile if it changed/was blank
            if request.user.telegram_id != telegram_id:
                request.user.telegram_id = telegram_id
                request.user.save(update_fields=['telegram_id'])
            return Response({"status": "success", "detail": "Test message sent", "file_id": res.get("file_id")})
        else:
            return Response(
                {"error": "Не удалось отправить сообщение через Telegram API", "detail": res.get("response")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
