from rest_framework import serializers
from apps.mailing.models import MailingTask

class MailingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingTask
        fields = [
            'id', 'organization', 'title', 'channel_type', 'message_ru', 'message_kz',
            'scheduled_at', 'audience_type', 'status',
            'has_image', 'image', 'tg_id_for_test', 'telegram_file_id',
            'total_recipients', 'sent_success', 'failed_count', 'unsubscribed_count',
            'last_processed_user_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'organization', 'total_recipients', 'sent_success',
            'failed_count', 'unsubscribed_count', 'last_processed_user_id',
            'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        channel_type = attrs.get('channel_type', getattr(self.instance, 'channel_type', MailingTask.CHANNEL_TELEGRAM))
        has_image = attrs.get('has_image', getattr(self.instance, 'has_image', False))
        title = attrs.get('title', getattr(self.instance, 'title', ''))
        message_ru = attrs.get('message_ru', getattr(self.instance, 'message_ru', ''))
        message_kz = attrs.get('message_kz', getattr(self.instance, 'message_kz', ''))

        if channel_type in [MailingTask.CHANNEL_GOOGLE_WALLET, MailingTask.CHANNEL_APPLE_WALLET]:
            if len(title) > 35:
                raise serializers.ValidationError({
                    'title': 'Заголовок push-уведомления для кошелька не должен превышать 35 символов.'
                })
            if len(message_ru) > 200:
                raise serializers.ValidationError({
                    'message_ru': 'Текст push-уведомления (RU) для кошелька не должен превышать 200 символов.'
                })
            if len(message_kz) > 200:
                raise serializers.ValidationError({
                    'message_kz': 'Текст push-уведомления (KZ) для кошелька не должен превышать 200 символов.'
                })
        elif has_image:
            if len(message_ru) > 1024:
                raise serializers.ValidationError({
                    'message_ru': 'Подпись к фото (RU) не должна превышать 1024 символа (ограничение Telegram API).'
                })
            if len(message_kz) > 1024:
                raise serializers.ValidationError({
                    'message_kz': 'Подпись к фото (KZ) не должна превышать 1024 символа (ограничение Telegram API).'
                })
        return attrs
