from django.urls import path
from apps.loyalty.consumers import LoyaltyConsumer

websocket_urlpatterns = [
    path('ws/loyalty/user_updates/<int:customer_id>/', LoyaltyConsumer.as_asgi()),
]
