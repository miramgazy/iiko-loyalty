from rest_framework import serializers
from django.utils.crypto import get_random_string
from apps.accounts.models import User, UserOrganization
from apps.core.models import Organization
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'address', 'branding', 'instagram_link', 'whatsapp_link', 'is_active', 'created_at']

class UserOrganizationSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = UserOrganization
        fields = ['organization', 'role']

class UserSerializer(serializers.ModelSerializer):
    memberships = UserOrganizationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'telegram_id', 'is_bot_subscribed', 'language', 'memberships', 'is_superuser']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = 'employee'
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        return data

class EmployeeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role']

    def get_role(self, obj):
        org_id = self.context.get('organization_id')
        membership = obj.memberships.filter(organization_id=org_id).first()
        return membership.role if membership else None

class EmployeeCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[
        (UserOrganization.ROLE_ORG_MANAGER, 'OrgManager'),
        (UserOrganization.ROLE_ORG_ADMIN, 'OrgAdmin')
    ], required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def create(self, validated_data):
        org_id = self.context.get('organization_id')
        org = Organization.objects.get(id=org_id)
        email = validated_data['email']
        password = validated_data['password']
        
        # Check if user already exists
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': validated_data['first_name'],
                'last_name': validated_data.get('last_name', ''),
                'is_staff': True
            }
        )
        
        user.set_password(password)
        if not user.is_staff:
            user.is_staff = True
        user.save()
                
        # Link to organization
        membership, created_membership = UserOrganization.objects.get_or_create(
            user=user,
            organization=org,
            defaults={'role': validated_data['role']}
        )
        
        if not created_membership:
            membership.role = validated_data['role']
            membership.save()
        
        user.created_membership = membership
        return user


class SuperAdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    organization_id = serializers.IntegerField(write_only=True)
    memberships = UserOrganizationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'first_name', 'last_name',
            'telegram_id', 'language', 'is_active', 'password',
            'organization_id', 'memberships'
        ]

    def validate(self, attrs):
        if not self.instance:
            if not attrs.get('password'):
                raise serializers.ValidationError({"password": "Пароль обязателен при создании пользователя."})
            if not attrs.get('organization_id'):
                raise serializers.ValidationError({"organization_id": "Организация обязательна при создании пользователя."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        org_id = validated_data.pop('organization_id')

        validated_data['is_staff'] = True

        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()

        # Link to organization as org_manager
        UserOrganization.objects.create(
            user=user,
            organization_id=org_id,
            role=UserOrganization.ROLE_ORG_MANAGER
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        org_id = validated_data.pop('organization_id', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        if org_id:
            # Update membership to only have the chosen organization as org_manager
            UserOrganization.objects.filter(user=instance).delete()
            UserOrganization.objects.create(
                user=instance,
                organization_id=org_id,
                role=UserOrganization.ROLE_ORG_MANAGER
            )

        return instance


