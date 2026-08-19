from django.db import models
from apps.core.models import Organization

class DailyOlapReport(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='daily_olap_reports')
    date = models.DateField("Дата отчета")
    
    revenue = models.DecimalField("Выручка", max_digits=12, decimal_places=2, default=0.0)
    cost = models.DecimalField("Себестоимость", max_digits=12, decimal_places=2, default=0.0)
    discounts = models.DecimalField("Скидки", max_digits=12, decimal_places=2, default=0.0)
    checks_count = models.IntegerField("Количество чеков", default=0)
    guests_count = models.IntegerField("Количество гостей", default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'date')
        verbose_name = "Дневной отчет OLAP"
        verbose_name_plural = "Дневные отчеты OLAP"

    def __str__(self):
        return f"{self.organization.name} - {self.date}: Выручка {self.revenue}"


class HourlyOlapReport(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='hourly_olap_reports')
    date = models.DateField("Дата отчета")
    hour = models.IntegerField("Час (0-23)")
    
    product_id = models.UUIDField("UUID Блюда/Товара")
    product_name = models.CharField("Название Блюда", max_length=255)
    quantity = models.DecimalField("Количество продаж", max_digits=10, decimal_places=3, default=0.0)
    revenue = models.DecimalField("Выручка", max_digits=12, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'date', 'hour', 'product_id')
        verbose_name = "Почасовые продажи блюда"
        verbose_name_plural = "Почасовые продажи блюд"

    def __str__(self):
        return f"{self.organization.name} - {self.date} H{self.hour}: {self.product_name} x {self.quantity}"


class IikoOlapPreset(models.Model):
    REPORT_TYPE_CHOICES = (
        ('daily_kpi', 'Дневные продажи для KPI (Системный)'),
        ('hourly_sales', 'Почасовые продажи блюд (Системный)'),
        ('custom', 'Пользовательский отчет'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='olap_presets')
    report_type_key = models.CharField("Тип отчета", max_length=50, choices=REPORT_TYPE_CHOICES, default='custom')
    name = models.CharField("Название отчета", max_length=255)
    description = models.TextField("Описание отчета", blank=True, null=True)
    preset_id = models.UUIDField("UUID пресета в iiko RMS")
    is_system = models.BooleanField("Системный отчет", default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'report_type_key'],
                condition=~models.Q(report_type_key='custom'),
                name='unique_system_preset_per_org'
            )
        ]
        verbose_name = "OLAP пресет iiko"
        verbose_name_plural = "OLAP пресеты iiko"

    def __str__(self):
        return f"{self.organization.name} - {self.name} ({self.preset_id})"

