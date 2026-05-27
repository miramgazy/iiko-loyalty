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
            'owner_email', 'temp_password'
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'temp_password']

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
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'address',
            'tg_bot_token', 'tg_bot_username', 'tma_name',
            'iiko_integration_type', 'iiko_api_base_url', 'iiko_api_login', 'iiko_organization_id', 'iiko_loyalty_program_id',
            'is_iiko_webhook_password_enabled', 'iiko_webhook_password',
            'google_issuer_id', 'google_loyalty_class_id',
            'branding', 'instagram_link', 'whatsapp_link'
        ]
        read_only_fields = ['id', 'slug']
