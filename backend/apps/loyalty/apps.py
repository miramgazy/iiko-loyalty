import sys
import threading
from django.apps import AppConfig

class LoyaltyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.loyalty'

    def ready(self):
        ignored_commands = {'migrate', 'makemigrations', 'test', 'collectstatic', 'shell', 'createsuperuser'}
        if any(cmd in sys.argv for cmd in ignored_commands):
            return

        def _auto_register_webhooks():
            import time
            time.sleep(3)
            try:
                from apps.loyalty.tasks import register_all_tg_webhooks
                register_all_tg_webhooks()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error auto-registering Telegram webhooks on startup: {e}")

        thread = threading.Thread(target=_auto_register_webhooks, daemon=True)
        thread.start()
