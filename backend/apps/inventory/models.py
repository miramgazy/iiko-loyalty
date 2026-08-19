from django.db import models
from apps.core.models import Organization

class ProductPurchaseHistory(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='purchase_histories')
    product_id = models.UUIDField("UUID Ингредиента/Товара")
    product_name = models.CharField("Название товара", max_length=255)
    
    supplier_id = models.UUIDField("UUID Поставщика", null=True, blank=True)
    supplier_name = models.CharField("Название Поставщика", max_length=255, blank=True, null=True)
    
    price = models.DecimalField("Закупочная цена за единицу", max_digits=10, decimal_places=2)
    quantity = models.DecimalField("Количество закупки", max_digits=10, decimal_places=3)
    date = models.DateField("Дата прихода")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "История закупки товара"
        verbose_name_plural = "История закупок товаров"
        ordering = ['-date']

    def __str__(self):
        return f"{self.product_name}: {self.price} x {self.quantity} ({self.date})"


class StopListHistory(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='stop_lists')
    product_id = models.UUIDField("UUID Блюда")
    product_name = models.CharField("Название Блюда", max_length=255)
    
    started_at = models.DateTimeField("Начало нахождения в стопе")
    ended_at = models.DateTimeField("Выход из стопа", null=True, blank=True)
    
    duration_seconds = models.IntegerField("Длительность простоя (сек)", null=True, blank=True)
    lost_revenue = models.DecimalField("Упущенная выручка", max_digits=12, decimal_places=2, default=0.0)
    lost_profit = models.DecimalField("Упущенная валовая прибыль", max_digits=12, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "История стоп-листов"
        verbose_name_plural = "История стоп-листов"
        ordering = ['-started_at']

    def __str__(self):
        status = f"с {self.started_at}" if not self.ended_at else f"длился {self.duration_seconds // 60} мин"
        return f"{self.product_name} - в стопе: {status}"


class ProductInventoryRule(models.Model):
    ROLE_CHOICES = (
        ('chef', 'Шеф-повар / Кухня'),
        ('barman', 'Бар-менеджер / Бар'),
        ('purchaser', 'Закупщик'),
        ('owner', 'Управляющий / Владелец'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='inventory_rules')
    product_id = models.UUIDField("UUID Ингредиента")
    product_name = models.CharField("Название Ингредиента", max_length=255)
    
    min_stock = models.DecimalField("Минимальный остаток (Min)", max_digits=10, decimal_places=3, default=0.0)
    max_stock = models.DecimalField("Максимальный остаток (Max)", max_digits=10, decimal_places=3, default=0.0)
    target_price = models.DecimalField("Плановая/Идеальная цена закупа", max_digits=10, decimal_places=2, default=0.0)
    
    responsible_role = models.CharField("Ответственная роль", max_length=20, choices=ROLE_CHOICES, default='chef')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'product_id')
        verbose_name = "Правило Min-Max остатков"
        verbose_name_plural = "Правила Min-Max остатков"

    def __str__(self):
        return f"{self.product_name} ({self.min_stock} - {self.max_stock})"


class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Черновик'),
        ('APPROVED', 'Утвержден'),
        ('SENT', 'Отправлен в iiko'),
        ('FAILED', 'Ошибка отправки'),
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier_id = models.UUIDField("UUID Поставщика", null=True, blank=True)
    supplier_name = models.CharField("Название Поставщика", max_length=255, blank=True, null=True)
    
    status = models.CharField("Статус заказа", max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    iiko_document_id = models.UUIDField("UUID Документа в iiko", null=True, blank=True)
    error_message = models.TextField("Сообщение об ошибке", blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заказ поставщику"
        verbose_name_plural = "Заказы поставщикам"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} - {self.supplier_name or 'Поставщик не выбран'} ({self.status})"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product_id = models.UUIDField("UUID Ингредиента")
    product_name = models.CharField("Название Ингредиента", max_length=255)
    quantity = models.DecimalField("Количество закупки", max_digits=10, decimal_places=3)
    price = models.DecimalField("Закупочная цена (из истории)", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Позиция заказа поставщику"
        verbose_name_plural = "Позиции заказов поставщикам"

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
