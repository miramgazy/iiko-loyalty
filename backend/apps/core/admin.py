from django.contrib import admin
from .models import Organization, Employee, WabaTriggerRule, WabaMessageLog

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_waba_enabled', 'iiko_integration_type', 'is_active', 'created_at')
    list_filter = ('is_waba_enabled', 'iiko_integration_type', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'tg_bot_username', 'iiko_organization_id', 'waba_business_account_id')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'address', 'is_active', 'created_at')
        }),
        ('Интеграция WhatsApp WABA', {
            'fields': ('is_waba_enabled', 'waba_access_token', 'waba_business_account_id', 'waba_phone_number_id')
        }),
        ('Интеграция Telegram & TMA', {
            'fields': ('tg_bot_token', 'tg_bot_username', 'tma_name', 'tma_direct_link')
        }),
        ('Интеграция iiko', {
            'fields': (
                'iiko_integration_type', 
                'iiko_api_base_url', 
                'iiko_api_login', 
                'iiko_app_id',
                'iiko_client_secret',
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

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'role', 'organization', 'is_active')
    list_filter = ('role', 'is_active', 'organization')
    search_fields = ('first_name', 'last_name', 'telegram_id')
    raw_id_fields = ('organization',)

@admin.register(WabaTriggerRule)
class WabaTriggerRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'organization', 'template_name', 'template_language', 'is_enabled')
    list_filter = ('event_type', 'is_enabled', 'organization')
    search_fields = ('name', 'template_name', 'organization__name')

@admin.register(WabaMessageLog)
class WabaMessageLogAdmin(admin.ModelAdmin):
    list_display = ('phone', 'template_name', 'organization', 'status', 'created_at')
    list_filter = ('status', 'template_name', 'organization', 'created_at')
    search_fields = ('phone', 'template_name', 'rendered_text', 'waba_message_id')
    readonly_fields = ('created_at',)
