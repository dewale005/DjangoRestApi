# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from webapp.api import models
from webapp.api import serializers


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


class StockMovementViewSet(TenantScopedViewSet):
    queryset = models.StockMovement.objects.all().order_by('-created_at')
    serializer_class = serializers.StockMovementSerializer


class PurchaseOrderViewSet(TenantScopedViewSet):
    queryset = models.PurchaseOrder.objects.all().order_by('-order_date')
    serializer_class = serializers.PurchaseOrderSerializer


class PurchaseOrderLineViewSet(TenantScopedViewSet):
    queryset = models.PurchaseOrderLine.objects.all().order_by('purchase_order_id')
    serializer_class = serializers.PurchaseOrderLineSerializer


class SalesOrderViewSet(TenantScopedViewSet):
    queryset = models.SalesOrder.objects.all().order_by('-order_date')
    serializer_class = serializers.SalesOrderSerializer


class SalesOrderLineViewSet(TenantScopedViewSet):
    queryset = models.SalesOrderLine.objects.all().order_by('sales_order_id')
    serializer_class = serializers.SalesOrderLineSerializer


class BillOfMaterialViewSet(TenantScopedViewSet):
    queryset = models.BillOfMaterial.objects.all().order_by('product_id')
    serializer_class = serializers.BillOfMaterialSerializer


class ManufacturingOrderViewSet(TenantScopedViewSet):
    queryset = models.ManufacturingOrder.objects.all().order_by('-created_at')
    serializer_class = serializers.ManufacturingOrderSerializer


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


class JournalLineViewSet(TenantScopedViewSet):
    queryset = models.JournalLine.objects.all().order_by('journal_entry_id')
    serializer_class = serializers.JournalLineSerializer


class LeadViewSet(TenantScopedViewSet):
    queryset = models.Lead.objects.all().order_by('-created_at')
    serializer_class = serializers.LeadSerializer
