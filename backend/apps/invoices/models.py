from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from pgvector.django import VectorField
from apps.core.models import Organization, Employee

User = get_user_model()


class Invoice(models.Model):
    SOURCE_CHOICES = (
        ('tma', 'Telegram Mini App'),
        ('web_admin', 'Веб-админка'),
    )

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_RECOGNIZED = 'recognized'
    STATUS_APPROVED = 'approved'
    STATUS_SENT_TO_IIKO = 'sent_to_iiko'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Ожидает обработки'),
        (STATUS_PROCESSING, 'Распознавание (AI)'),
        (STATUS_RECOGNIZED, 'Распознан / Требует сверки'),
        (STATUS_APPROVED, 'Согласован'),
        (STATUS_SENT_TO_IIKO, 'Отправлен в iiko (Черновик)'),
        (STATUS_FAILED, 'Ошибка обработки'),
    )

    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='invoices',
        verbose_name="Организация"
    )
    source = models.CharField("Источник загрузки", max_length=20, choices=SOURCE_CHOICES, default='web_admin')
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='uploaded_invoices',
        verbose_name="Загружено пользователем"
    )
    uploaded_by_employee = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='uploaded_invoices',
        verbose_name="Загружено сотрудником TMA"
    )

    internal_number = models.CharField("Внутренний номер черновика", max_length=60, unique=True, db_index=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    error_message = models.TextField("Текст ошибки", blank=True, default="")

    # Склад оприходования в iiko
    iiko_store_id = models.UUIDField("UUID Склада iiko", null=True, blank=True)
    iiko_store_name = models.CharField("Название склада iiko", max_length=255, blank=True, default="")

    # Метаданные из накладной (извлеченные AI)
    invoice_number = models.CharField("Номер накладной поставщика", max_length=100, blank=True, default="")
    invoice_date = models.DateField("Дата накладной", null=True, blank=True)
    raw_supplier_name = models.CharField("Поставщик из документа", max_length=255, blank=True, default="")
    raw_supplier_inn = models.CharField("ИНН/БИН поставщика", max_length=50, blank=True, default="")
    total_sum = models.DecimalField("Итоговая сумма по документу", max_digits=12, decimal_places=2, null=True, blank=True)
    vat_sum = models.DecimalField("Сумма НДС", max_digits=12, decimal_places=2, null=True, blank=True)

    # Сопоставление с контрагентом iiko
    iiko_supplier_id = models.UUIDField("UUID Поставщика iiko", null=True, blank=True)
    iiko_supplier_name = models.CharField("Название поставщика в iiko", max_length=255, blank=True, default="")

    # Идентификаторы созданного документа в iiko Server
    iiko_document_id = models.CharField("UUID документа в iiko", max_length=100, blank=True, default="")
    iiko_document_number = models.CharField("Учетный номер в iiko", max_length=100, blank=True, default="")
    sent_to_iiko_at = models.DateTimeField("Дата отправки в iiko", null=True, blank=True)

    # Исходный структурированный ответ Vision LLM
    raw_llm_response = models.JSONField("Сырой ответ LLM", default=dict, blank=True)

    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        verbose_name = "Приходная накладная"
        verbose_name_plural = "Приходные накладные"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.internal_number:
            prefix = "НАКЛ" if self.source == 'tma' else "INV"
            date_str = timezone.now().strftime("%Y%m%d")
            import secrets
            random_suffix = secrets.token_hex(3).upper()
            self.internal_number = f"{prefix}-{date_str}-{random_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        doc_num = self.invoice_number or self.internal_number
        supplier = self.iiko_supplier_name or self.raw_supplier_name or "Поставщик не определен"
        return f"{doc_num} ({supplier}) - {self.get_status_display()}"


class InvoiceImage(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='images', verbose_name="Накладная")
    image = models.FileField("Файл/Фото накладной", upload_to='invoices/%Y/%m/%d/')
    page_number = models.PositiveIntegerField("Номер страницы", default=1)
    is_pdf = models.BooleanField("Является PDF", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Страница накладной"
        verbose_name_plural = "Страницы накладной"
        ordering = ['page_number', 'id']

    def __str__(self):
        return f"{self.invoice.internal_number} - Стр. {self.page_number}"


class InvoiceItem(models.Model):
    MATCH_STATUS_GREEN = 'green'
    MATCH_STATUS_YELLOW = 'yellow'
    MATCH_STATUS_RED = 'red'

    MATCH_STATUS_CHOICES = (
        (MATCH_STATUS_GREEN, 'Точное совпадение (Зеленый)'),
        (MATCH_STATUS_YELLOW, 'Вероятное совпадение (Желтый)'),
        (MATCH_STATUS_RED, 'Не найдено / Требует выбора (Красный)'),
    )

    MATCH_SOURCE_CHOICES = (
        ('knowledge_base', 'База знаний (Алиас)'),
        ('fuzzy', 'Нечеткий поиск (RapidFuzz)'),
        ('llm', 'Vision LLM подсказка'),
        ('manual', 'Выбрано вручную'),
    )

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name="Накладная")
    num = models.PositiveIntegerField("Номер строки в документе", default=1)

    # Исходные данные из накладной (OCR/LLM)
    raw_name = models.CharField("Наименование из накладной", max_length=255)
    clean_name = models.CharField("Очищенное наименование (AI)", max_length=255, blank=True, default="")
    raw_unit = models.CharField("Единица из накладной", max_length=50, blank=True, default="")
    raw_amount = models.DecimalField("Количество по накладной", max_digits=12, decimal_places=3, default=0.0)
    raw_price = models.DecimalField("Цена по накладной", max_digits=12, decimal_places=2, default=0.0)
    raw_sum = models.DecimalField("Сумма по накладной", max_digits=12, decimal_places=2, default=0.0)
    raw_vat_percent = models.DecimalField("Процент НДС", max_digits=6, decimal_places=2, null=True, blank=True)

    # Сопоставление с номенклатурой iiko
    iiko_product_id = models.UUIDField("UUID Товара в iiko", null=True, blank=True)
    iiko_product_name = models.CharField("Товар в iiko", max_length=255, blank=True, default="")
    iiko_product_code = models.CharField("Артикул в iiko", max_length=100, blank=True, default="")
    confidence = models.DecimalField("Уверенность сопоставления", max_digits=5, decimal_places=2, default=0.0)
    match_status = models.CharField("Цветовой статус", max_length=10, choices=MATCH_STATUS_CHOICES, default=MATCH_STATUS_RED)
    match_source = models.CharField("Источник совпадения", max_length=20, choices=MATCH_SOURCE_CHOICES, default='manual')
    candidates = models.JSONField("Топ похожих товаров iiko", default=list, blank=True)

    # Фасовка и пересчет для складского учета iiko
    packaging_coefficient = models.DecimalField(
        "Коэффициент фасовки (базовых единиц iiko в 1 упаковке)",
        max_digits=12,
        decimal_places=3,
        default=1.000
    )
    iiko_container_id = models.UUIDField("UUID Фасовки iiko", null=True, blank=True)
    iiko_container_name = models.CharField("Название фасовки iiko", max_length=100, blank=True, default="")

    iiko_amount = models.DecimalField("Количество в базовых единицах iiko", max_digits=12, decimal_places=3, default=0.0)
    iiko_price = models.DecimalField("Цена за 1 базовую единицу iiko", max_digits=12, decimal_places=2, default=0.0)
    iiko_sum = models.DecimalField("Итоговая сумма строки в iiko", max_digits=12, decimal_places=2, default=0.0)
    sum_diff = models.DecimalField("Погрешность копеек (raw_sum - iiko_sum)", max_digits=10, decimal_places=2, default=0.0)

    class Meta:
        verbose_name = "Строка приходной накладной"
        verbose_name_plural = "Строки приходной накладной"
        ordering = ['num', 'id']

    def __str__(self):
        return f"#{self.num}: {self.raw_name} -> {self.iiko_product_name or 'НЕ СОПОСТАВЛЕНО'}"


class SupplierProductAlias(models.Model):
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='product_aliases',
        verbose_name="Организация"
    )
    supplier_id = models.UUIDField("UUID Поставщика в iiko", null=True, blank=True, db_index=True)
    supplier_name = models.CharField("Название поставщика", max_length=255, blank=True, default="")

    raw_product_name = models.CharField("Сырое наименование из накладной", max_length=255, db_index=True)
    normalized_raw_name = models.CharField("Нормализованное наименование", max_length=255, db_index=True)

    iiko_product_id = models.UUIDField("UUID Товара в iiko")
    iiko_product_name = models.CharField("Товар в iiko", max_length=255)

    default_packaging_coefficient = models.DecimalField(
        "Коэффициент фасовки по умолчанию",
        max_digits=12,
        decimal_places=3,
        default=1.000
    )
    default_container_id = models.UUIDField("UUID Фасовки iiko", null=True, blank=True)
    default_container_name = models.CharField("Название фасовки", max_length=100, blank=True, default="")

    usage_count = models.PositiveIntegerField("Количество подтверждений", default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "База знаний: Связка поставщика и товара"
        verbose_name_plural = "База знаний: Связки поставщиков и товаров"
        unique_together = ('organization', 'supplier_id', 'normalized_raw_name')
        ordering = ['-usage_count', '-last_used_at']

    def __str__(self):
        return f"{self.raw_product_name} -> {self.iiko_product_name} ({self.supplier_name})"


class IikoProductEmbedding(models.Model):
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='product_embeddings',
        verbose_name="Организация"
    )
    iiko_product_id = models.UUIDField("UUID Товара в iiko", db_index=True)
    name = models.CharField("Наименование товара в iiko", max_length=500)
    clean_name = models.CharField("Очищенное / осмысленное имя", max_length=500, blank=True, default="")
    code = models.CharField("Артикул / код товара", max_length=100, blank=True, default="")
    unit = models.CharField("Единица измерения", max_length=50, blank=True, default="")
    product_type = models.CharField("Тип номенклатуры (GOODS, DISH, PREPARED)", max_length=50, blank=True, default="GOODS")
    containers = models.JSONField("Доступные фасовки", default=list, blank=True)

    embedding = VectorField("Вектор эмбеддинга", dimensions=768, null=True, blank=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Векторный эмбеддинг товара iiko"
        verbose_name_plural = "Векторные эмбеддинги товаров iiko"
        unique_together = ('organization', 'iiko_product_id')
        indexes = [
            models.Index(fields=['organization', 'clean_name']),
        ]

    def __str__(self):
        return f"{self.name} [{self.organization.name}]"

