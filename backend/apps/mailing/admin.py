from django.contrib import admin
from .models import MailingTask

@admin.register(MailingTask)
class MailingTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'status', 'scheduled_at', 'audience_type', 'total_recipients', 'sent_success')
    list_filter = ('status', 'audience_type', 'organization', 'scheduled_at')
    search_fields = ('title', 'message_ru', 'message_kz')
    raw_id_fields = ('organization',)
    readonly_fields = ('created_at', 'updated_at', 'total_recipients', 'sent_success', 'failed_count', 'unsubscribed_count', 'last_processed_user_id')
    
    fieldsets = (
        ('Детали рассылки', {
            'fields': ('title', 'organization', 'audience_type', 'status', 'scheduled_at')
        }),
        ('Тексты сообщений', {
            'fields': ('message_ru', 'message_kz')
        }),
        ('Статистика отправки', {
            'fields': ('total_recipients', 'sent_success', 'failed_count', 'unsubscribed_count')
        }),
        ('Системные поля', {
            'fields': ('last_processed_user_id', 'created_at', 'updated_at')
        }),
    )
