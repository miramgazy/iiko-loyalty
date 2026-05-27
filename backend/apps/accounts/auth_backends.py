import re
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from apps.core.utils import normalize_phone

User = get_user_model()

class MultiMethodBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email') or kwargs.get('phone')

        if not username:
            return None

        normalized_phone = normalize_phone(username)

        try:
            user = User.objects.get(
                Q(username__iexact=username) |
                Q(email__iexact=username) |
                Q(phone=normalized_phone)
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

class MultiModelJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_type = validated_token.get("user_type", "employee")
        user_id = validated_token.get("user_id")

        if user_type == "customer":
            from apps.loyalty.models import Customer
            try:
                customer = Customer.objects.get(pk=user_id)
                return customer
            except Customer.DoesNotExist:
                raise AuthenticationFailed("Customer not found", code="user_not_found")
        else:
            try:
                user = User.objects.get(pk=user_id)
                return user
            except User.DoesNotExist:
                raise AuthenticationFailed("User not found", code="user_not_found")
