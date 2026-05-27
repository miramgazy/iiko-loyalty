from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import Organization

class User(AbstractUser):
    phone = models.CharField("Телефон сотрудника", max_length=20, blank=True)
    telegram_id = models.BigIntegerField("Telegram ID", null=True, blank=True)
    is_bot_subscribed = models.BooleanField("Подписан на бота", null=True, blank=True, default=None)
    language = models.CharField("Язык", max_length=10, default='ru', choices=[('ru', 'Русский'), ('kz', 'Қазақша')])

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

class UserOrganization(models.Model):
    ROLE_SUPERUSER = 'superuser'      # Разработчик / Владелец SaaS
    ROLE_SUPERADMIN = 'superadmin'    # Администратор платформы (поддержка)
    ROLE_ORG_MANAGER = 'org_manager'  # Владелец / Управляющий конкретной ресторанной сети
    ROLE_ORG_ADMIN = 'org_admin'      # Администратор конкретной точки / ресторана
    
    ROLE_CHOICES = [
        (ROLE_SUPERUSER, 'SuperUser'),
        (ROLE_SUPERADMIN, 'SuperAdmin'),
        (ROLE_ORG_MANAGER, 'OrgManager'),
        (ROLE_ORG_ADMIN, 'OrgAdmin'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to=models.Q(is_staff=True), 
        related_name='memberships'
    )
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='staff_memberships'
    )
    role = models.CharField("Роль в организации", max_length=20, choices=ROLE_CHOICES)
    
    class Meta:
        unique_together = ('user', 'organization')
