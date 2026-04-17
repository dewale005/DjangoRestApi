from django.contrib.auth.models import User, Group
from rest_framework import serializers
from webapp.api import models


class UserSerializers(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializers(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tenant
        fields = '__all__'


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Partner
        fields = '__all__'


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Warehouse
        fields = '__all__'


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductCategory
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = '__all__'


class StockLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StockLevel
        fields = '__all__'


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StockMovement
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PurchaseOrder
        fields = '__all__'


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PurchaseOrderLine
        fields = '__all__'


class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SalesOrder
        fields = '__all__'


class SalesOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SalesOrderLine
        fields = '__all__'


class BillOfMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BillOfMaterial
        fields = '__all__'


class ManufacturingOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManufacturingOrder
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Employee
        fields = '__all__'


class PayrollEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PayrollEntry
        fields = '__all__'


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Account
        fields = '__all__'


class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JournalEntry
        fields = '__all__'


class JournalLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JournalLine
        fields = '__all__'


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lead
        fields = '__all__'


class IdempotencyKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IdempotencyKey
        fields = '__all__'


class OutboxEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OutboxEvent
        fields = '__all__'


class PosTerminalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PosTerminal
        fields = '__all__'


class PosSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PosSession
        fields = '__all__'


class PosSaleLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PosSaleLine
        fields = '__all__'


class PosPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PosPayment
        fields = '__all__'


class PosSaleSerializer(serializers.ModelSerializer):
    lines = PosSaleLineSerializer(many=True, read_only=True)
    payments = PosPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = models.PosSale
        fields = '__all__'
