from rest_framework import serializers
from apps.mailing.models import MailingTask

class MailingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingTask
        fields = [
            'id', 'organization', 'title', 'message_ru', 'message_kz',
            'scheduled_at', 'audience_type', 'status', 'total_recipients',
            'sent_success', 'failed_count', 'unsubscribed_count',
            'last_processed_user_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'organization', 'total_recipients', 'sent_success',
            'failed_count', 'unsubscribed_count', 'last_processed_user_id',
            'created_at', 'updated_at'
        ]
