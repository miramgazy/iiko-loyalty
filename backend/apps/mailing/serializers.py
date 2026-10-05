from rest_framework import serializers
from apps.mailing.models import MailingTask

class MailingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingTask
        fields = [
            'id', 'organization', 'title', 'message_ru', 'message_kz',
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
        has_image = attrs.get('has_image', getattr(self.instance, 'has_image', False))
        message_ru = attrs.get('message_ru', getattr(self.instance, 'message_ru', ''))
        message_kz = attrs.get('message_kz', getattr(self.instance, 'message_kz', ''))

        if has_image:
            if len(message_ru) > 1024:
                raise serializers.ValidationError({
                    'message_ru': 'Подпись к фото (RU) не должна превышать 1024 символа (ограничение Telegram API).'
                })
            if len(message_kz) > 1024:
                raise serializers.ValidationError({
                    'message_kz': 'Подпись к фото (KZ) не должна превышать 1024 символа (ограничение Telegram API).'
                })
        return attrs
