from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from apps.core.models import Organization
from apps.accounts.models import UserOrganization

User = get_user_model()

class SuperAdminOrganizationSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(write_only=True, required=True)
    temp_password = serializers.CharField(read_only=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'is_active', 'created_at', 
            'owner_email', 'temp_password',
            'is_loyalty_enabled', 'is_analytics_enabled', 'is_ai_agent_enabled'
        ]
        read_only_fields = ['id', 'created_at', 'temp_password']

    def create(self, validated_data):
        owner_email = validated_data.pop('owner_email')
        
        # Create organization
        organization = Organization.objects.create(**validated_data)
        
        # Find or create owner user
        user, created = User.objects.get_or_create(
            email=owner_email,
            defaults={
                'username': owner_email,
                'is_staff': True
            }
        )
        
        temp_password = None
        if created:
            temp_password = get_random_string(length=12)
            user.set_password(temp_password)
            user.save()
        else:
            if not user.is_staff:
                user.is_staff = True
                user.save()
                
        # Link user to organization as OrgManager
        UserOrganization.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={'role': UserOrganization.ROLE_ORG_MANAGER}
        )
        
        if temp_password:
            organization.temp_password = temp_password
            
        return organization

class OrganizationSettingsSerializer(serializers.ModelSerializer):
    is_waba_configured = serializers.BooleanField(read_only=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'address',
            'tg_bot_token', 'tg_bot_username', 'tma_name', 'tma_direct_link',
            'is_waba_enabled', 'waba_access_token', 'waba_business_account_id', 'waba_phone_number_id',
            'is_waba_configured',
            'iiko_integration_type', 'iiko_api_base_url', 'iiko_api_login', 'iiko_app_id', 'iiko_client_secret', 'iiko_organization_id', 'iiko_loyalty_program_id',
            'is_iiko_webhook_password_enabled', 'iiko_webhook_password',
            'iiko_server_url', 'iiko_server_login', 'iiko_server_password',
            'is_google_wallet_enabled', 'google_issuer_id', 'google_loyalty_class_id', 'google_wallet_settings',
            'is_apple_wallet_enabled', 'apple_pass_type_id', 'apple_team_id', 'apple_wallet_settings',
            'is_web_onboarding_enabled', 'web_onboarding_settings',
            'branding', 'instagram_link', 'whatsapp_link',
            'is_loyalty_enabled', 'is_analytics_enabled', 'is_ai_agent_enabled',
            'llm_provider', 'llm_model_name', 'llm_api_key', 'llm_system_prompt'
        ]
        read_only_fields = ['id', 'slug', 'is_waba_configured', 'is_loyalty_enabled', 'is_analytics_enabled', 'is_ai_agent_enabled']

    def validate(self, attrs):
        is_onboarding = attrs.get('is_web_onboarding_enabled')
        if is_onboarding is None and self.instance:
            is_onboarding = self.instance.is_web_onboarding_enabled

        if is_onboarding:
            is_waba_enabled = attrs.get('is_waba_enabled') if 'is_waba_enabled' in attrs else (self.instance.is_waba_enabled if self.instance else False)
            waba_token = attrs.get('waba_access_token') if 'waba_access_token' in attrs else (self.instance.waba_access_token if self.instance else None)
            waba_phone_id = attrs.get('waba_phone_number_id') if 'waba_phone_number_id' in attrs else (self.instance.waba_phone_number_id if self.instance else None)

            if waba_token == '••••••••' and self.instance and self.instance.waba_access_token:
                waba_token = self.instance.waba_access_token

            if not (is_waba_enabled and waba_token and waba_phone_id):
                raise serializers.ValidationError({
                    'is_web_onboarding_enabled': 'Для включения страницы онбординга необходимо сначала настроить и включить WABA (WhatsApp Business API).'
                })

        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Mask sensitive keys
        for field in ['waba_access_token', 'llm_api_key', 'iiko_api_login', 'iiko_app_id', 'iiko_client_secret', 'iiko_webhook_password', 'iiko_server_password']:
            if getattr(instance, field, None):
                data[field] = '••••••••'
            else:
                data[field] = ''
        return data

    def update(self, instance, validated_data):
        # Prevent overwriting with masked placeholders
        for field in ['waba_access_token', 'llm_api_key', 'iiko_api_login', 'iiko_app_id', 'iiko_client_secret', 'iiko_webhook_password', 'iiko_server_password']:
            if field in validated_data:
                val = validated_data[field]
                if val == '••••••••':
                    validated_data.pop(field)
        return super().update(instance, validated_data)


from apps.core.models import WabaTriggerRule, WabaMessageLog

class WabaTriggerRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WabaTriggerRule
        fields = [
            'id', 'name', 'event_type', 'is_enabled',
            'template_name', 'template_language', 'parameter_mappings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WabaMessageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WabaMessageLog
        fields = [
            'id', 'phone', 'message_type', 'template_name', 'language',
            'parameters', 'rendered_text', 'waba_message_id', 'status',
            'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

from apps.core.models import Employee

class TmaEmployeeSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True, required=False)

    class Meta:
        model = Employee
        fields = ['id', 'first_name', 'last_name', 'telegram_id', 'role', 'is_active']
        read_only_fields = ['id']
