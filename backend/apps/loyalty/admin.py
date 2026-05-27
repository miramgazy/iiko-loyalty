from django.contrib import admin
from .models import Customer, IikoWebhookLog, LoyaltyProgram, Visit, CustomerWallet

class CustomerWalletInline(admin.TabularInline):
    model = CustomerWallet
    extra = 0
    readonly_fields = ('created_at', 'updated_at')

class VisitInline(admin.TabularInline):
    model = Visit
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'telegram_id', 'loyalty_balance', 'organization', 'created_at')
    list_filter = ('organization', 'is_bot_subscribed', 'is_active', 'language', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'telegram_id', 'email', 'iiko_customer_id', 'wallet_barcode')
    readonly_fields = ('created_at', 'updated_at', 'wallet_barcode')
    raw_id_fields = ('organization',)
    inlines = [CustomerWalletInline, VisitInline]
    
    fieldsets = (
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'birthday', 'language')
        }),
        ('Связи & Статус', {
            'fields': ('organization', 'telegram_id', 'is_bot_subscribed', 'is_active')
        }),
        ('Баланс & Карты', {
            'fields': ('loyalty_balance', 'wallet_barcode', 'google_wallet_object_id')
        }),
        ('Интеграция iiko', {
            'fields': ('iiko_customer_id', 'iiko_card_number', 'iiko_card_id', 'iiko_categories')
        }),
        ('Системные даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(IikoWebhookLog)
class IikoWebhookLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'organization_id', 'status', 'created_at')
    list_filter = ('status', 'event_type', 'created_at')
    search_fields = ('organization_id', 'event_type', 'error_message')
    readonly_fields = ('organization_id', 'event_type', 'payload', 'status', 'error_message', 'created_at')
    
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'created_at', 'updated_at')
    list_filter = ('organization', 'created_at')
    search_fields = ('title', 'title_kz', 'description', 'description_kz')
    raw_id_fields = ('organization',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('customer', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'customer__organization')
    search_fields = ('customer__first_name', 'customer__last_name', 'customer__phone')
    raw_id_fields = ('customer',)
    readonly_fields = ('created_at',)

@admin.register(CustomerWallet)
class CustomerWalletAdmin(admin.ModelAdmin):
    list_display = ('customer', 'name', 'balance', 'wallet_type', 'updated_at')
    list_filter = ('wallet_type', 'customer__organization')
    search_fields = ('customer__first_name', 'customer__last_name', 'customer__phone', 'name')
    raw_id_fields = ('customer',)
    readonly_fields = ('created_at', 'updated_at')
