import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.core.models import Organization
from apps.core.serializers import OrganizationSettingsSerializer

org = Organization(
    name="Test Org",
    slug="test-org",
    tg_bot_token="123:test",
    tg_bot_username="testbot"
)
org.save()

data = {
    "name": "Updated Org",
    "address": "",
    "tg_bot_username": "testbot",
    "tma_name": "",
    "iiko_integration_type": "iiko_transport",
    "iiko_api_base_url": "https://api-ru.iiko.services/api/1",
    "iiko_organization_id": None,
    "iiko_loyalty_program_id": None
}

serializer = OrganizationSettingsSerializer(org, data=data, partial=True)
print("Is valid:", serializer.is_valid())
if not serializer.is_valid():
    print("Errors:", serializer.errors)
else:
    serializer.save()
    print("Saved successfully!")
