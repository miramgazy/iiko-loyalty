from django.urls import path
from apps.loyalty.views import IikoWebhookView

urlpatterns = [
    path('iiko/webhook/', IikoWebhookView.as_view(), name='iiko_webhook'),
]
