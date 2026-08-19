from rest_framework import serializers
from apps.inventory.models import (
    ProductPurchaseHistory, StopListHistory,
    ProductInventoryRule, PurchaseOrder, PurchaseOrderItem
)

class ProductInventoryRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventoryRule
        fields = ['id', 'product_id', 'product_name', 'min_stock', 'max_stock', 'target_price', 'responsible_role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'product_id', 'product_name', 'quantity', 'price']
        read_only_fields = ['id']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'supplier_id', 'supplier_name', 'status', 'iiko_document_id', 'error_message', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'iiko_document_id', 'error_message', 'created_at', 'updated_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        # Get organization_id from context
        org_id = self.context['organization_id']
        order = PurchaseOrder.objects.create(organization_id=org_id, **validated_data)
        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        instance.supplier_id = validated_data.get('supplier_id', instance.supplier_id)
        instance.supplier_name = validated_data.get('supplier_name', instance.supplier_name)
        instance.save()
        
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                PurchaseOrderItem.objects.create(purchase_order=instance, **item_data)
        return instance


class StopListHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StopListHistory
        fields = ['id', 'product_id', 'product_name', 'started_at', 'ended_at', 'duration_seconds', 'lost_revenue', 'lost_profit']
