from django.db import models
from apps.core.fields import EncryptedCharField

class Organization(models.Model):
    name = models.CharField("Название ресторана/сети", max_length=255)
    slug = models.SlugField("Уникальный Slug", max_length=100, unique=True)
    address = models.TextField("Фактический адрес", blank=True)
    
    # Telegram Bot интеграция
    tg_bot_token = EncryptedCharField("Токен Telegram-бота", max_length=255, unique=True, blank=True, null=True)
    tg_bot_username = models.CharField(
        "Username Telegram-бота (без @)", 
        max_length=100, 
        unique=True, 
        db_index=True,
        blank=True,
        null=True
    )
    tma_name = models.CharField("Короткое имя Mini App в BotFather", max_length=100, blank=True)
    INTEGRATION_TYPE_CHOICES = (
        ('iiko_transport', 'iiko Cloud API (Transport)'),
        ('iiko_card', 'iikoCard (Legacy)'),
    )
    
    # iiko Cloud API интеграция
    iiko_integration_type = models.CharField(
        "Тип интеграции с iiko",
        max_length=20,
        choices=INTEGRATION_TYPE_CHOICES,
        default='iiko_transport'
    )
    iiko_api_base_url = models.URLField(
        "iiko API Base URL", 
        default="https://api-ru.iiko.services/api/1"
    )
    iiko_api_login = EncryptedCharField("iiko API Login (API-ключ)", max_length=255, blank=True)
    iiko_app_id = EncryptedCharField("iiko App ID", max_length=255, blank=True)
    iiko_client_secret = EncryptedCharField("iiko Client Secret", max_length=255, blank=True)
    iiko_organization_id = models.UUIDField("iiko Organization ID", null=True, blank=True)
    iiko_loyalty_program_id = models.UUIDField("iiko Loyalty Program ID", null=True, blank=True)
    
    # iiko Server REST API (RMS / Chain)
    iiko_server_url = models.URLField("iiko Server URL", blank=True, null=True)
    iiko_server_login = EncryptedCharField("iiko Server Login", max_length=255, blank=True, null=True)
    iiko_server_password = EncryptedCharField("iiko Server Password", max_length=255, blank=True, null=True)
    
    # Настройки Webhook iiko
    is_iiko_webhook_password_enabled = models.BooleanField("Включить проверку пароля для Webhook", default=False)
    iiko_webhook_password = models.CharField("Пароль вебхука iiko (subscriptionPassword)", max_length=255, blank=True, null=True)
    
    # Кастомизация Mini App
    branding = models.JSONField(
        "Настройки брендинга (цвета, логотип, приветствие)",
        default=dict,
        blank=True,
        help_text="Пример: {'design_color': '#FF5733', 'greeting_text': 'Добро пожаловать в Бургерную!'}"
    )
    
    # Google Wallet интеграция
    google_issuer_id = models.CharField("Google Issuer ID", max_length=50, null=True, blank=True)
    google_loyalty_class_id = models.CharField("Google Loyalty Class ID", max_length=100, null=True, blank=True)

    # Социальные сети
    instagram_link = models.URLField("Ссылка на Instagram", blank=True, null=True)
    whatsapp_link = models.URLField("Ссылка на WhatsApp", blank=True, null=True)
    tma_direct_link = models.URLField("Прямая ссылка на TMA", blank=True, null=True)

    # Модули (переключатели)
    is_loyalty_enabled = models.BooleanField("Включена система лояльности", default=True)
    is_analytics_enabled = models.BooleanField("Включена аналитика и закупки", default=False)
    is_ai_agent_enabled = models.BooleanField("Включен AI-агент", default=False)

    # Настройки LLM
    LLM_PROVIDER_CHOICES = (
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic Claude'),
        ('gemini', 'Google Gemini'),
        ('deepseek', 'DeepSeek'),
    )
    llm_provider = models.CharField(
        "Провайдер LLM",
        max_length=20,
        choices=LLM_PROVIDER_CHOICES,
        default='openai'
    )
    llm_model_name = models.CharField(
        "Название модели",
        max_length=100,
        default='gpt-4o-mini',
        blank=True
    )
    llm_api_key = EncryptedCharField(
        "API ключ LLM",
        max_length=255,
        blank=True,
        null=True
    )
    llm_system_prompt = models.TextField(
        "Системный промпт для AI-агента",
        blank=True,
        null=True,
        default="Вы — полезный AI-финансовый аналитик и закупщик для ресторана. Помогайте управлять заказами, анализировать фудкост, цены и упущенную выручку."
    )

    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_tma_link(self):
        if self.tma_direct_link:
            return self.tma_direct_link
        if self.tg_bot_username and self.tma_name:
            return f"https://t.me/{self.tg_bot_username}/{self.tma_name}"
        return ""

    def __str__(self):
        return self.name

class Employee(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Владелец'),
        ('manager', 'Менеджер'),
        ('cashier', 'Кассир'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='employees')
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    telegram_id = models.BigIntegerField("Telegram ID", null=True, blank=True, db_index=True)
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default='owner')
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()}) - {self.organization.name}"


class AlertLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='alert_logs')
    alert_type = models.CharField("Тип оповещения", max_length=50)
    entity_id = models.UUIDField("ID сущности (например, товара)", null=True, blank=True)
    message = models.TextField("Текст оповещения")
    created_at = models.DateTimeField("Дата отправки", auto_now_add=True)

    class Meta:
        verbose_name = "Лог оповещения"
        verbose_name_plural = "Логи оповещений"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.name} - {self.alert_type} ({self.created_at})"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Organization)
def on_organization_save(sender, instance, created, **kwargs):
    if instance.tg_bot_token:
        from apps.loyalty.tasks import register_tg_webhook
        import logging
        try:
            register_tg_webhook.delay(instance.id)
        except Exception as e:
            logging.error(f"Failed to queue register_tg_webhook: {e}")

