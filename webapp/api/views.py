# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from webapp.api import models
from webapp.api import serializers
from webapp.api.services import (
    PosService,
    InventoryService,
    ProcurementService,
    ManufacturingService,
    SalesService,
    FinanceService,
)


class TenantScopedViewSet(viewsets.ModelViewSet):
    tenant_field = 'tenant_id'

    def get_tenant_id(self):
        tenant_id = self.request.query_params.get('tenant_id') or self.request.data.get('tenant')
        if tenant_id:
            return tenant_id
        raise ValidationError('tenant_id query param (or tenant in payload) is required for this endpoint.')

    def get_queryset(self):
        queryset = super(TenantScopedViewSet, self).get_queryset()
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return queryset.filter(**{self.tenant_field: tenant_id})
        return queryset.none()

    def perform_create(self, serializer):
        tenant_id = self.get_tenant_id()
        serializer.save(tenant_id=tenant_id)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializers


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializers


class TenantViewSet(viewsets.ModelViewSet):
    queryset = models.Tenant.objects.all().order_by('name')
    serializer_class = serializers.TenantSerializer


class PartnerViewSet(TenantScopedViewSet):
    queryset = models.Partner.objects.all().order_by('name')
    serializer_class = serializers.PartnerSerializer


class WarehouseViewSet(TenantScopedViewSet):
    queryset = models.Warehouse.objects.all().order_by('name')
    serializer_class = serializers.WarehouseSerializer


class ProductCategoryViewSet(TenantScopedViewSet):
    queryset = models.ProductCategory.objects.all().order_by('name')
    serializer_class = serializers.ProductCategorySerializer


class ProductViewSet(TenantScopedViewSet):
    queryset = models.Product.objects.all().order_by('name')
    serializer_class = serializers.ProductSerializer


class StockLevelViewSet(TenantScopedViewSet):
    queryset = models.StockLevel.objects.all().order_by('warehouse_id')
    serializer_class = serializers.StockLevelSerializer

    @action(detail=False, methods=['post'])
    def adjust(self, request):
        tenant_id = self.get_tenant_id()
        stock_level = InventoryService.adjust_stock(
            tenant_id=tenant_id,
            warehouse_id=request.data.get('warehouse'),
            product_id=request.data.get('product'),
            quantity_delta=request.data.get('quantity_delta'),
            reference=request.data.get('reference', ''),
            notes=request.data.get('notes', 'Manual adjustment'),
        )
        return Response(serializers.StockLevelSerializer(stock_level).data)


class StockMovementViewSet(TenantScopedViewSet):
    queryset = models.StockMovement.objects.all().order_by('-created_at')
    serializer_class = serializers.StockMovementSerializer


class PurchaseOrderViewSet(TenantScopedViewSet):
    queryset = models.PurchaseOrder.objects.all().order_by('-order_date')
    serializer_class = serializers.PurchaseOrderSerializer

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        tenant_id = self.get_tenant_id()
        purchase_order = ProcurementService.receive_purchase_order(
            tenant_id=tenant_id,
            purchase_order_id=pk,
            warehouse_id=request.data.get('warehouse'),
        )
        return Response(serializers.PurchaseOrderSerializer(purchase_order).data)


class PurchaseOrderLineViewSet(TenantScopedViewSet):
    queryset = models.PurchaseOrderLine.objects.all().order_by('purchase_order_id')
    serializer_class = serializers.PurchaseOrderLineSerializer


class SalesOrderViewSet(TenantScopedViewSet):
    queryset = models.SalesOrder.objects.all().order_by('-order_date')
    serializer_class = serializers.SalesOrderSerializer

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        tenant_id = self.get_tenant_id()
        sales_order = SalesService.deliver_sales_order(
            tenant_id=tenant_id,
            sales_order_id=pk,
            warehouse_id=request.data.get('warehouse'),
        )
        return Response(serializers.SalesOrderSerializer(sales_order).data)


class SalesOrderLineViewSet(TenantScopedViewSet):
    queryset = models.SalesOrderLine.objects.all().order_by('sales_order_id')
    serializer_class = serializers.SalesOrderLineSerializer


class BillOfMaterialViewSet(TenantScopedViewSet):
    queryset = models.BillOfMaterial.objects.all().order_by('product_id')
    serializer_class = serializers.BillOfMaterialSerializer


class ManufacturingOrderViewSet(TenantScopedViewSet):
    queryset = models.ManufacturingOrder.objects.all().order_by('-created_at')
    serializer_class = serializers.ManufacturingOrderSerializer

    @action(detail=True, methods=['post'])
    def record_output(self, request, pk=None):
        tenant_id = self.get_tenant_id()
        manufacturing_order = ManufacturingService.record_output(
            tenant_id=tenant_id,
            manufacturing_order_id=pk,
            warehouse_id=request.data.get('warehouse'),
            output_quantity=request.data.get('output_quantity'),
        )
        return Response(serializers.ManufacturingOrderSerializer(manufacturing_order).data)


class EmployeeViewSet(TenantScopedViewSet):
    queryset = models.Employee.objects.all().order_by('full_name')
    serializer_class = serializers.EmployeeSerializer


class PayrollEntryViewSet(TenantScopedViewSet):
    queryset = models.PayrollEntry.objects.all().order_by('-period')
    serializer_class = serializers.PayrollEntrySerializer


class AccountViewSet(TenantScopedViewSet):
    queryset = models.Account.objects.all().order_by('code')
    serializer_class = serializers.AccountSerializer


class JournalEntryViewSet(TenantScopedViewSet):
    queryset = models.JournalEntry.objects.all().order_by('-posted_on')
    serializer_class = serializers.JournalEntrySerializer

    @action(detail=False, methods=['post'])
    def post_inventory(self, request):
        tenant_id = self.get_tenant_id()
        journal_entry = FinanceService.post_inventory_adjustment_journal(
            tenant_id=tenant_id,
            reference=request.data.get('reference', 'manual_adjustment'),
            amount=request.data.get('amount'),
        )
        return Response(serializers.JournalEntrySerializer(journal_entry).data, status=status.HTTP_201_CREATED)


class JournalLineViewSet(TenantScopedViewSet):
    queryset = models.JournalLine.objects.all().order_by('journal_entry_id')
    serializer_class = serializers.JournalLineSerializer


class LeadViewSet(TenantScopedViewSet):
    queryset = models.Lead.objects.all().order_by('-created_at')
    serializer_class = serializers.LeadSerializer


class PosTerminalViewSet(TenantScopedViewSet):
    queryset = models.PosTerminal.objects.all().order_by('name')
    serializer_class = serializers.PosTerminalSerializer


class PosSessionViewSet(TenantScopedViewSet):
    queryset = models.PosSession.objects.all().order_by('-created_at')
    serializer_class = serializers.PosSessionSerializer


class PosSaleViewSet(TenantScopedViewSet):
    queryset = models.PosSale.objects.all().order_by('-created_at')
    serializer_class = serializers.PosSaleSerializer

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        tenant_id = request.query_params.get('tenant_id') or request.data.get('tenant')
        if not tenant_id:
            raise ValidationError('tenant_id is required.')
        amount = request.data.get('amount')
        sale = PosService.refund(tenant_id=tenant_id, sale_id=pk, amount=amount)
        return Response(serializers.PosSaleSerializer(sale).data)


class PosSessionOpenApi(APIView):
    def post(self, request):
        tenant_id = request.data.get('tenant')
        terminal_id = request.data.get('terminal')
        opening_float = request.data.get('opening_float', '0.00')
        session = PosService.open_session(tenant_id=tenant_id, terminal_id=terminal_id, opening_float=opening_float)
        return Response(serializers.PosSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class PosCheckoutApi(APIView):
    def post(self, request):
        tenant_id = request.data.get('tenant')
        session_id = request.data.get('session')
        idempotency_key = request.headers.get('Idempotency-Key') or request.data.get('idempotency_key')
        lines = request.data.get('lines', [])
        payments = request.data.get('payments', [])
        customer_id = request.data.get('customer')

        sale, is_duplicate = PosService.checkout(
            tenant_id=tenant_id,
            session_id=session_id,
            idempotency_key=idempotency_key,
            lines=lines,
            payments=payments,
            customer_id=customer_id,
        )
        response_data = serializers.PosSaleSerializer(sale).data
        response_data['idempotent_replay'] = is_duplicate
        return Response(response_data, status=status.HTTP_200_OK if is_duplicate else status.HTTP_201_CREATED)
