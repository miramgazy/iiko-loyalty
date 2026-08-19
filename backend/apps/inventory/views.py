from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.core.models import Organization
from apps.accounts.permissions import IsOrgEmployee
from apps.inventory.models import ProductInventoryRule, PurchaseOrder, StopListHistory
from apps.inventory.serializers import (
    ProductInventoryRuleSerializer, PurchaseOrderSerializer, StopListHistorySerializer
)
from apps.inventory.services import calculate_price_drift

class ProductInventoryRuleViewSet(viewsets.ModelViewSet):
    serializer_class = ProductInventoryRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get_queryset(self):
        org_id = self.kwargs.get('organization_id')
        return ProductInventoryRule.objects.filter(organization_id=org_id).order_by('product_name')

    def perform_create(self, serializer):
        org_id = self.kwargs.get('organization_id')
        org = get_object_or_404(Organization, id=org_id)
        serializer.save(organization=org)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get_queryset(self):
        org_id = self.kwargs.get('organization_id')
        return PurchaseOrder.objects.filter(organization_id=org_id).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization_id'] = self.kwargs.get('organization_id')
        return context


class PriceDriftListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        if not org.is_analytics_enabled:
            return Response({"error": "Module 'analytics' is not enabled for this organization"}, status=status.HTTP_403_FORBIDDEN)
            
        drift_data = calculate_price_drift(org)
        return Response(drift_data)


class StopListHistoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def get(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        if not org.is_analytics_enabled:
            return Response({"error": "Module 'analytics' is not enabled for this organization"}, status=status.HTTP_403_FORBIDDEN)
            
        stop_lists = StopListHistory.objects.filter(organization=org).order_by('-started_at')
        serializer = StopListHistorySerializer(stop_lists, many=True)
        return Response(serializer.data)


class ApprovePurchaseOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def post(self, request, organization_id, pk, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        if not org.is_analytics_enabled:
            return Response({"error": "Module 'analytics' is not enabled for this organization"}, status=status.HTTP_403_FORBIDDEN)
            
        order = get_object_or_404(PurchaseOrder, id=pk, organization=org)
        if order.status != 'DRAFT':
            return Response({"error": "Only draft orders can be approved"}, status=status.HTTP_400_BAD_REQUEST)
            
        order.status = 'APPROVED'
        order.save()
        
        import logging
        logger = logging.getLogger(__name__)
        from apps.inventory.services import IikoInventoryService
        try:
            inventory_service = IikoInventoryService(org)
            iiko_doc_id = inventory_service.create_purchase_order(order)
            
            order.status = 'SENT'
            order.iiko_document_id = iiko_doc_id
            order.save()
        except Exception as e:
            logger.error(f"Failed to submit purchase order to iiko: {e}", exc_info=True)
            order.status = 'FAILED'
            order.error_message = str(e)
            order.save()
            return Response({
                "error": f"Ошибка отправки заказа в iiko: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "status": "success",
            "message": "Order approved and successfully sent to iiko",
            "iiko_document_id": order.iiko_document_id
        })
