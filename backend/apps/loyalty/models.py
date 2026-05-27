from django.db import models
from apps.core.models import Organization

class Customer(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='customers')
    telegram_id = models.BigIntegerField("Telegram ID", null=True, blank=True)
    is_bot_subscribed = models.BooleanField("Согласие на рассылку", null=True, blank=True, default=None)
    phone = models.CharField("Номер телефона", max_length=20, blank=True, null=True)
    iiko_customer_id = models.UUIDField("iiko Customer UUID", null=True, blank=True, db_index=True)
    iiko_card_number = models.CharField("Номер карты iiko", max_length=50, blank=True, null=True)
    iiko_card_id = models.UUIDField("iiko Card UUID", null=True, blank=True)
    iiko_categories = models.JSONField("Категории в iiko", default=list, blank=True)
    
    # Личные данные
    first_name = models.CharField("Имя", max_length=150, blank=True)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    email = models.EmailField("E-mail", blank=True, null=True)
    birthday = models.DateField("Дата рождения", null=True, blank=True)
    
    # Кэш баланса из iiko
    loyalty_balance = models.DecimalField("Баланс баллов", max_digits=10, decimal_places=2, default=0.00)
    
    # Wallet / Digital Cards
    google_wallet_object_id = models.CharField("Google Wallet Object ID", max_length=100, null=True, blank=True)
    wallet_barcode = models.CharField("Штрих-код", max_length=50, unique=True, blank=True, null=True)

    LANGUAGE_CHOICES = (
        ('ru', 'Русский'),
        ('kz', 'Қазақша'),
    )
    language = models.CharField("Язык", max_length=2, choices=LANGUAGE_CHOICES, default='ru')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        unique_together = (
            ('organization', 'telegram_id'),
            ('organization', 'phone'),
        )

    def save(self, *args, **kwargs):
        if not self.wallet_barcode:
            import random
            import string
            self.wallet_barcode = ''.join(random.choices(string.digits, k=13))
        super().save(*args, **kwargs)

    @property
    def is_onboarded(self):
        return bool(self.phone)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone or 'Нет телефона'}) - {self.organization.name}"

class IikoWebhookLog(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Ожидает обработки'),
        ('SUCCESS', 'Успешно'),
        ('FAILED', 'Ошибка'),
    )
    organization_id = models.UUIDField("iiko Organization ID", null=True, blank=True)
    event_type = models.CharField("Тип события", max_length=100)
    payload = models.JSONField("Тело вебхука (JSON)")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField("Сообщение об ошибке", blank=True, null=True)
    created_at = models.DateTimeField("Дата получения", auto_now_add=True)

    class Meta:
        verbose_name = "Лог вебхука iiko"
        verbose_name_plural = "Логи вебхуков iiko"

    def __str__(self):
        return f"Webhook {self.event_type} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class LoyaltyProgram(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='loyalty_programs')
    title = models.CharField("Заголовок программы лояльности (RU)", max_length=255)
    title_kz = models.CharField("Заголовок программы лояльности (KZ)", max_length=255, blank=True, null=True)
    description = models.TextField("Описание программы лояльности (RU)")
    description_kz = models.TextField("Описание программы лояльности (KZ)", blank=True, null=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Программа лояльности"
        verbose_name_plural = "Программы лояльности"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.organization.name}"

class Visit(models.Model):
    STATUS_CHOICES = (
        ('confirmed', 'Подтвержден'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='visits')
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField("Дата визита", auto_now_add=True)

    class Meta:
        verbose_name = "Визит"
        verbose_name_plural = "Визиты"

    def __str__(self):
        return f"Visit of {self.customer.first_name} ({self.status}) - {self.created_at.strftime('%Y-%m-%d')}"

class CustomerWallet(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='wallets')
    wallet_id = models.UUIDField("iiko Wallet UUID", db_index=True)
    name = models.CharField("Название программы лояльности / кошелька", max_length=255)
    balance = models.DecimalField("Баланс баллов", max_digits=10, decimal_places=2, default=0.00)
    wallet_type = models.IntegerField("Тип кошелька", default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Кошелек клиента"
        verbose_name_plural = "Кошельки клиентов"
        unique_together = ('customer', 'wallet_id')

    def __str__(self):
        return f"{self.name}: {self.balance} ({self.customer.first_name})"
