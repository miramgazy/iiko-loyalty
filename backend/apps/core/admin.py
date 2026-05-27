from django.contrib import admin
from .models import Organization

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'iiko_integration_type', 'is_active', 'created_at')
    list_filter = ('iiko_integration_type', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'tg_bot_username', 'iiko_organization_id')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'address', 'is_active', 'created_at')
        }),
        ('Интеграция Telegram & TMA', {
            'fields': ('tg_bot_token', 'tg_bot_username', 'tma_name', 'tma_direct_link')
        }),
        ('Интеграция iiko', {
            'fields': (
                'iiko_integration_type', 
                'iiko_api_base_url', 
                'iiko_api_login', 
                'iiko_organization_id', 
                'iiko_loyalty_program_id',
                'is_iiko_webhook_password_enabled',
                'iiko_webhook_password'
            )
        }),
        ('Кастомизация & Ссылки', {
            'fields': ('branding', 'instagram_link', 'whatsapp_link')
        }),
        ('Google Wallet', {
            'fields': ('google_issuer_id', 'google_loyalty_class_id')
        }),
    )
