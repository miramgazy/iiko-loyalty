from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserOrganization

class UserOrganizationInline(admin.TabularInline):
    model = UserOrganization
    extra = 1
    raw_id_fields = ('organization',)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone', 'telegram_id', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'language', 'is_bot_subscribed', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'telegram_id')
    ordering = ('-date_joined',)
    
    inlines = [UserOrganizationInline]

    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Telegram & Loyalty Info'), {'fields': ('phone', 'telegram_id', 'is_bot_subscribed', 'language')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Telegram & Loyalty Info'), {
            'classes': ('wide',),
            'fields': ('phone', 'telegram_id', 'is_bot_subscribed', 'language'),
        }),
    )

@admin.register(UserOrganization)
class UserOrganizationAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role')
    list_filter = ('role', 'organization')
    search_fields = ('user__username', 'user__email', 'user__phone', 'organization__name')
    raw_id_fields = ('user', 'organization')
