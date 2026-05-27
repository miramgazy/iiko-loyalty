from django.contrib import admin
from django.urls import path, include
from apps.accounts.views import SetWebhookView

urlpatterns = [
    path('administrator/', admin.site.urls),
    path('api/core/', include('apps.core.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/loyalty/', include('apps.loyalty.urls')),
    path('api/v1/integrations/', include('apps.loyalty.integration_urls')),
    
    # Mailings app routes
    path('api/mailings/', include('apps.mailing.urls')),
    
    # Organization webhook setting
    path('api/organization/set-webhook/', SetWebhookView.as_view(), name='set_webhook'),
]

