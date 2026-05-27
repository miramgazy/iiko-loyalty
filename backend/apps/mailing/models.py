from django.db import models
from apps.core.models import Organization

class MailingTask(models.Model):
    AUDIENCE_ALL = 'all'
    AUDIENCE_ACTIVE = 'active'
    AUDIENCE_INACTIVE = 'inactive'

    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL, 'Все клиенты'),
        (AUDIENCE_ACTIVE, 'Активные (за последние 60 дней)'),
        (AUDIENCE_INACTIVE, 'Неактивные (более 60 дней)'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'
    STATUS_ERROR = 'error'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_SCHEDULED, 'Запланирована'),
        (STATUS_IN_PROGRESS, 'В процессе'),
        (STATUS_DONE, 'Завершена'),
        (STATUS_ERROR, 'Ошибка'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='mailing_tasks')
    title = models.CharField("Название рассылки", max_length=255)
    message_ru = models.TextField("Сообщение (RU)")
    message_kz = models.TextField("Сообщение (KZ)")
    scheduled_at = models.DateTimeField("Время отправки")
    audience_type = models.CharField("Целевой сегмент", max_length=20, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    # Analytics fields
    total_recipients = models.PositiveIntegerField("Размер целевой аудитории", default=0)
    sent_success = models.PositiveIntegerField("Успешно отправлено", default=0)
    failed_count = models.PositiveIntegerField("Ошибок отправки", default=0)
    unsubscribed_count = models.PositiveIntegerField("Заблокировавших бота", default=0)

    # Pagination cursor
    last_processed_user_id = models.IntegerField("ID последнего обработанного пользователя", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"{self.title} ({self.status}) - {self.organization.name}"
