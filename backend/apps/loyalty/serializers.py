from rest_framework import serializers
from apps.loyalty.models import Customer, LoyaltyProgram, CustomerWallet
from apps.accounts.serializers import OrganizationSerializer

class CustomerWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerWallet
        fields = ['id', 'wallet_id', 'name', 'balance', 'wallet_type']

class CustomerSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    is_onboarded = serializers.BooleanField(read_only=True)
    wallets = CustomerWalletSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 
            'telegram_id', 
            'is_bot_subscribed',
            'phone', 
            'iiko_customer_id', 
            'iiko_card_number',
            'iiko_categories',
            'first_name', 
            'last_name', 
            'email', 
            'birthday', 
            'loyalty_balance',
            'language',
            'is_onboarded', 
            'organization',
            'wallets'
        ]
        read_only_fields = ['id', 'telegram_id', 'phone', 'iiko_customer_id', 'iiko_card_number', 'iiko_categories', 'loyalty_balance', 'is_onboarded', 'organization', 'wallets']

class LoyaltyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyProgram
        fields = ['id', 'title', 'title_kz', 'description', 'description_kz', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
