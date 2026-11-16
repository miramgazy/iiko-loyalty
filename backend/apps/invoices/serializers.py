from rest_framework import serializers
from apps.invoices.models import Invoice, InvoiceImage, InvoiceItem, SupplierProductAlias


class InvoiceImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceImage
        fields = ['id', 'image', 'image_url', 'page_number', 'is_pdf', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'num', 'raw_name', 'clean_name', 'raw_unit', 'raw_amount', 'raw_price', 'raw_sum', 'raw_vat_percent',
            'iiko_product_id', 'iiko_product_name', 'iiko_product_code',
            'confidence', 'match_status', 'match_source', 'candidates',
            'packaging_coefficient', 'iiko_container_id', 'iiko_container_name',
            'iiko_amount', 'iiko_price', 'iiko_sum', 'sum_diff'
        ]


class InvoiceListSerializer(serializers.ModelSerializer):
    images_count = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    author = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'internal_number', 'invoice_number', 'invoice_date',
            'raw_supplier_name', 'raw_supplier_inn', 'iiko_supplier_id', 'iiko_supplier_name',
            'iiko_store_id', 'iiko_store_name',
            'total_sum', 'vat_sum', 'status', 'status_display', 'source', 'source_display',
            'author',
            'error_message', 'iiko_document_number', 'sent_to_iiko_at',
            'images_count', 'items_count', 'created_at', 'updated_at'
        ]

    def get_images_count(self, obj):
        return obj.images.count()

    def get_items_count(self, obj):
        return obj.items.count()

    def get_author(self, obj):
        if obj.uploaded_by_employee:
            emp = obj.uploaded_by_employee
            name = f"{emp.first_name} {emp.last_name}".strip() or "Сотрудник"
            role_disp = emp.get_role_display()
            return {
                "id": emp.id,
                "type": "employee",
                "name": name,
                "role": role_disp,
                "display": f"{name} ({role_disp})" if role_disp else name
            }
        elif obj.uploaded_by:
            u = obj.uploaded_by
            name = u.get_full_name() or u.username
            return {
                "id": u.id,
                "type": "user",
                "name": name,
                "role": "Веб-администратор",
                "display": name
            }
        return {
            "id": None,
            "type": "system",
            "name": "Система",
            "role": "",
            "display": "Система"
        }


class InvoiceDetailSerializer(serializers.ModelSerializer):
    images = InvoiceImageSerializer(many=True, read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    author = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'organization_id', 'internal_number', 'invoice_number', 'invoice_date',
            'raw_supplier_name', 'raw_supplier_inn', 'iiko_supplier_id', 'iiko_supplier_name',
            'iiko_store_id', 'iiko_store_name',
            'total_sum', 'vat_sum', 'status', 'status_display', 'source', 'source_display',
            'author',
            'error_message', 'iiko_document_id', 'iiko_document_number', 'sent_to_iiko_at',
            'raw_llm_response', 'images', 'items', 'created_at', 'updated_at'
        ]

    def get_author(self, obj):
        if obj.uploaded_by_employee:
            emp = obj.uploaded_by_employee
            name = f"{emp.first_name} {emp.last_name}".strip() or "Сотрудник"
            role_disp = emp.get_role_display()
            return {
                "id": emp.id,
                "type": "employee",
                "name": name,
                "role": role_disp,
                "display": f"{name} ({role_disp})" if role_disp else name
            }
        elif obj.uploaded_by:
            u = obj.uploaded_by
            name = u.get_full_name() or u.username
            return {
                "id": u.id,
                "type": "user",
                "name": name,
                "role": "Веб-администратор",
                "display": name
            }
        return {
            "id": None,
            "type": "system",
            "name": "Система",
            "role": "",
            "display": "Система"
        }


class SupplierProductAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierProductAlias
        fields = [
            'id', 'supplier_id', 'supplier_name', 'raw_product_name', 'normalized_raw_name',
            'iiko_product_id', 'iiko_product_name',
            'default_packaging_coefficient', 'default_container_id', 'default_container_name',
            'usage_count', 'created_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'normalized_raw_name', 'usage_count', 'created_at', 'last_used_at']
