from django.contrib import admin
from apps.invoices.models import Invoice, InvoiceImage, InvoiceItem, SupplierProductAlias


class InvoiceImageInline(admin.TabularInline):
    model = InvoiceImage
    extra = 0
    readonly_fields = ['page_number', 'is_pdf', 'created_at']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = [
        'num', 'raw_name', 'raw_amount', 'raw_price', 'raw_sum',
        'iiko_product_name', 'match_status', 'packaging_coefficient',
        'iiko_amount', 'iiko_price', 'iiko_sum', 'sum_diff'
    ]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'internal_number', 'invoice_number', 'organization', 'raw_supplier_name',
        'total_sum', 'status', 'source', 'sent_to_iiko_at', 'created_at'
    ]
    list_filter = ['status', 'source', 'organization', 'created_at']
    search_fields = ['internal_number', 'invoice_number', 'raw_supplier_name', 'iiko_supplier_name']
    inlines = [InvoiceImageInline, InvoiceItemInline]


@admin.register(SupplierProductAlias)
class SupplierProductAliasAdmin(admin.ModelAdmin):
    list_display = [
        'raw_product_name', 'iiko_product_name', 'supplier_name',
        'organization', 'default_packaging_coefficient', 'usage_count', 'last_used_at'
    ]
    list_filter = ['organization', 'supplier_name']
    search_fields = ['raw_product_name', 'iiko_product_name', 'supplier_name']
