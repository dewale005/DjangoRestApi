# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tenant(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    allow_negative_stock = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class TenantScopedModel(TimeStampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Partner(TenantScopedModel):
    CUSTOMER = 'customer'
    VENDOR = 'vendor'
    BOTH = 'both'
    PARTNER_TYPE_CHOICES = (
        (CUSTOMER, 'Customer'),
        (VENDOR, 'Vendor'),
        (BOTH, 'Both'),
    )

    name = models.CharField(max_length=120)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPE_CHOICES, default=CUSTOMER)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name


class Warehouse(TenantScopedModel):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40)
    address = models.TextField(blank=True)

    class Meta:
        unique_together = ('tenant', 'code')

    def __str__(self):
        return self.code


class ProductCategory(TenantScopedModel):
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name


class Product(TenantScopedModel):
    sku = models.CharField(max_length=40)
    name = models.CharField(max_length=160)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ('tenant', 'sku')

    def __str__(self):
        return '%s - %s' % (self.sku, self.name)


class StockLevel(TenantScopedModel):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_levels')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_levels')
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        unique_together = ('tenant', 'warehouse', 'product')


class StockMovement(TenantScopedModel):
    IN = 'in'
    OUT = 'out'
    TRANSFER = 'transfer'
    MOVEMENT_CHOICES = ((IN, 'IN'), (OUT, 'OUT'), (TRANSFER, 'TRANSFER'))

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=60, blank=True)
    notes = models.TextField(blank=True)


class PurchaseOrder(TenantScopedModel):
    DRAFT = 'draft'
    APPROVED = 'approved'
    RECEIVED = 'received'
    STATUS_CHOICES = ((DRAFT, 'Draft'), (APPROVED, 'Approved'), (RECEIVED, 'Received'))

    po_number = models.CharField(max_length=40)
    vendor = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    order_date = models.DateField()

    class Meta:
        unique_together = ('tenant', 'po_number')


class PurchaseOrderLine(TenantScopedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)


class SalesOrder(TenantScopedModel):
    DRAFT = 'draft'
    CONFIRMED = 'confirmed'
    DELIVERED = 'delivered'
    STATUS_CHOICES = ((DRAFT, 'Draft'), (CONFIRMED, 'Confirmed'), (DELIVERED, 'Delivered'))

    so_number = models.CharField(max_length=40)
    customer = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name='sales_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    order_date = models.DateField()

    class Meta:
        unique_together = ('tenant', 'so_number')


class SalesOrderLine(TenantScopedModel):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)


class BillOfMaterial(TenantScopedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_headers')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_components')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)


class ManufacturingOrder(TenantScopedModel):
    DRAFT = 'draft'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'
    STATUS_CHOICES = ((DRAFT, 'Draft'), (IN_PROGRESS, 'In Progress'), (DONE, 'Done'))

    mo_number = models.CharField(max_length=40)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)

    class Meta:
        unique_together = ('tenant', 'mo_number')


class Employee(TenantScopedModel):
    employee_code = models.CharField(max_length=40)
    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    department = models.CharField(max_length=80, blank=True)

    class Meta:
        unique_together = ('tenant', 'employee_code')


class PayrollEntry(TenantScopedModel):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='payroll_entries')
    period = models.CharField(max_length=20)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Account(TenantScopedModel):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ('tenant', 'code')


class JournalEntry(TenantScopedModel):
    entry_number = models.CharField(max_length=40)
    description = models.CharField(max_length=255, blank=True)
    posted_on = models.DateField()

    class Meta:
        unique_together = ('tenant', 'entry_number')


class JournalLine(TenantScopedModel):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Lead(TenantScopedModel):
    name = models.CharField(max_length=120)
    source = models.CharField(max_length=120, blank=True)
    expected_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_converted = models.BooleanField(default=False)

class IdempotencyKey(TenantScopedModel):
    key = models.CharField(max_length=120)
    endpoint = models.CharField(max_length=120)
    status_code = models.IntegerField(default=200)
    response_payload = models.TextField(blank=True)

    class Meta:
        unique_together = ('tenant', 'key', 'endpoint')


class OutboxEvent(TenantScopedModel):
    PENDING = 'pending'
    PUBLISHED = 'published'
    FAILED = 'failed'
    STATUS_CHOICES = ((PENDING, 'Pending'), (PUBLISHED, 'Published'), (FAILED, 'Failed'))

    aggregate_type = models.CharField(max_length=60)
    aggregate_id = models.CharField(max_length=64)
    event_type = models.CharField(max_length=120)
    payload = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    published_at = models.DateTimeField(null=True, blank=True)


class PosTerminal(TenantScopedModel):
    name = models.CharField(max_length=80)
    store_name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tenant', 'name')


class PosSession(TenantScopedModel):
    PENDING_OPEN = 'pending_open'
    OPEN = 'open'
    SUSPENDED = 'suspended'
    CLOSING = 'closing'
    CLOSED = 'closed'
    RECONCILED = 'reconciled'
    STATUS_CHOICES = (
        (PENDING_OPEN, 'Pending Open'),
        (OPEN, 'Open'),
        (SUSPENDED, 'Suspended'),
        (CLOSING, 'Closing'),
        (CLOSED, 'Closed'),
        (RECONCILED, 'Reconciled'),
    )

    terminal = models.ForeignKey(PosTerminal, on_delete=models.PROTECT, related_name='sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING_OPEN)
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class PosSale(TenantScopedModel):
    DRAFT_CART = 'draft_cart'
    SUSPENDED = 'suspended'
    FINALIZED = 'finalized'
    PAID = 'paid'
    REFUNDED_PARTIAL = 'refunded_partial'
    REFUNDED_FULL = 'refunded_full'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (DRAFT_CART, 'Draft Cart'),
        (SUSPENDED, 'Suspended'),
        (FINALIZED, 'Finalized'),
        (PAID, 'Paid'),
        (REFUNDED_PARTIAL, 'Refunded Partial'),
        (REFUNDED_FULL, 'Refunded Full'),
        (CANCELLED, 'Cancelled'),
    )

    sale_number = models.CharField(max_length=64)
    session = models.ForeignKey(PosSession, on_delete=models.PROTECT, related_name='sales')
    customer = models.ForeignKey(Partner, null=True, blank=True, on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=120)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=PAID)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    refunded_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        unique_together = (('tenant', 'sale_number'), ('tenant', 'idempotency_key'))


class PosSaleLine(TenantScopedModel):
    sale = models.ForeignKey(PosSale, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)


class PosPayment(TenantScopedModel):
    CASH = 'cash'
    CARD = 'card'
    TRANSFER = 'transfer'
    METHOD_CHOICES = ((CASH, 'Cash'), (CARD, 'Card'), (TRANSFER, 'Transfer'))

    sale = models.ForeignKey(PosSale, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=120, blank=True)
