# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient
from webapp.api import models


class TenantIsolationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.tenant_a = models.Tenant.objects.create(name='Tenant A', code='TA')
        self.tenant_b = models.Tenant.objects.create(name='Tenant B', code='TB')
        self.cat_a = models.ProductCategory.objects.create(tenant=self.tenant_a, name='Cat A')
        self.cat_b = models.ProductCategory.objects.create(tenant=self.tenant_b, name='Cat B')
        models.Product.objects.create(tenant=self.tenant_a, sku='SKU-A', name='Product A', category=self.cat_a)
        models.Product.objects.create(tenant=self.tenant_b, sku='SKU-B', name='Product B', category=self.cat_b)

    def test_products_filtered_by_tenant(self):
        response = self.client.get('/products/?tenant_id=%s' % self.tenant_a.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sku'], 'SKU-A')


class PosCheckoutTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.tenant = models.Tenant.objects.create(name='Tenant POS', code='TP')
        self.category = models.ProductCategory.objects.create(tenant=self.tenant, name='General')
        self.product = models.Product.objects.create(
            tenant=self.tenant,
            sku='POS-001',
            name='POS Product',
            category=self.category,
            sale_price=Decimal('10.00'),
        )
        self.warehouse = models.Warehouse.objects.create(tenant=self.tenant, name='Main', code='MAIN')
        self.stock = models.StockLevel.objects.create(
            tenant=self.tenant,
            warehouse=self.warehouse,
            product=self.product,
            quantity=Decimal('10.00'),
        )
        self.terminal = models.PosTerminal.objects.create(tenant=self.tenant, name='T1', store_name='Store 1')
        self.session = models.PosSession.objects.create(
            tenant=self.tenant,
            terminal=self.terminal,
            status=models.PosSession.OPEN,
            opening_float=Decimal('100.00'),
        )

    def _checkout_payload(self):
        return {
            'tenant': self.tenant.id,
            'session': self.session.id,
            'idempotency_key': 'checkout-key-1',
            'lines': [
                {
                    'product': self.product.id,
                    'warehouse': self.warehouse.id,
                    'quantity': '2.00',
                    'unit_price': '10.00',
                    'tax_amount': '1.00'
                }
            ],
            'payments': [
                {
                    'payment_method': 'cash',
                    'amount': '21.00'
                }
            ]
        }

    def test_checkout_deducts_stock_and_creates_outbox(self):
        response = self.client.post('/pos/sales/checkout/', self._checkout_payload(), format='json')
        self.assertEqual(response.status_code, 201)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal('8.00'))
        self.assertEqual(models.OutboxEvent.objects.filter(tenant=self.tenant).count(), 1)

    def test_checkout_is_idempotent(self):
        first = self.client.post('/pos/sales/checkout/', self._checkout_payload(), format='json')
        second = self.client.post('/pos/sales/checkout/', self._checkout_payload(), format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data['idempotent_replay'])

        self.assertEqual(models.PosSale.objects.filter(tenant=self.tenant).count(), 1)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal('8.00'))

    def test_refund_returns_stock(self):
        checkout = self.client.post('/pos/sales/checkout/', self._checkout_payload(), format='json')
        sale_id = checkout.data['id']

        refund = self.client.post('/pos-sales/%s/refund/?tenant_id=%s' % (sale_id, self.tenant.id), {
            'amount': '21.00'
        }, format='json')
        self.assertEqual(refund.status_code, 200)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal('10.00'))

    def test_negative_stock_blocked(self):
        payload = self._checkout_payload()
        payload['lines'][0]['quantity'] = '20.00'
        response = self.client.post('/pos/sales/checkout/', payload, format='json')
        self.assertEqual(response.status_code, 400)


class ServicesWorkflowTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.tenant = models.Tenant.objects.create(name='Tenant Workflow', code='TW')
        self.category = models.ProductCategory.objects.create(tenant=self.tenant, name='Raw Material')
        self.component = models.Product.objects.create(
            tenant=self.tenant,
            sku='RM-1',
            name='Raw Material 1',
            category=self.category,
            sale_price=Decimal('2.00'),
        )
        self.finished = models.Product.objects.create(
            tenant=self.tenant,
            sku='FG-1',
            name='Finished Good 1',
            category=self.category,
            sale_price=Decimal('15.00'),
        )
        self.warehouse = models.Warehouse.objects.create(tenant=self.tenant, name='Central', code='CENT')
        models.StockLevel.objects.create(
            tenant=self.tenant,
            warehouse=self.warehouse,
            product=self.component,
            quantity=Decimal('100.00'),
        )
        models.StockLevel.objects.create(
            tenant=self.tenant,
            warehouse=self.warehouse,
            product=self.finished,
            quantity=Decimal('0.00'),
        )
        self.vendor = models.Partner.objects.create(
            tenant=self.tenant,
            name='Vendor A',
            partner_type=models.Partner.VENDOR,
        )
        self.customer = models.Partner.objects.create(
            tenant=self.tenant,
            name='Customer A',
            partner_type=models.Partner.CUSTOMER,
        )
        self.account_1 = models.Account.objects.create(tenant=self.tenant, code='1000', name='Inventory')
        self.account_2 = models.Account.objects.create(tenant=self.tenant, code='5000', name='COGS')

    def test_stock_adjust_endpoint(self):
        response = self.client.post('/stock-levels/adjust/?tenant_id=%s' % self.tenant.id, {
            'warehouse': self.warehouse.id,
            'product': self.finished.id,
            'quantity_delta': '5.00',
            'reference': 'ADJ-1',
            'notes': 'Manual increment',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        stock = models.StockLevel.objects.get(tenant=self.tenant, warehouse=self.warehouse, product=self.finished)
        self.assertEqual(stock.quantity, Decimal('5.00'))

    def test_purchase_order_receive_endpoint(self):
        po = models.PurchaseOrder.objects.create(
            tenant=self.tenant,
            po_number='PO-1',
            vendor=self.vendor,
            order_date='2026-01-01',
        )
        models.PurchaseOrderLine.objects.create(
            tenant=self.tenant,
            purchase_order=po,
            product=self.finished,
            quantity=Decimal('8.00'),
            unit_price=Decimal('3.00'),
        )
        response = self.client.post('/purchase-orders/%s/receive/?tenant_id=%s' % (po.id, self.tenant.id), {
            'warehouse': self.warehouse.id,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        po.refresh_from_db()
        self.assertEqual(po.status, models.PurchaseOrder.RECEIVED)
        stock = models.StockLevel.objects.get(tenant=self.tenant, warehouse=self.warehouse, product=self.finished)
        self.assertEqual(stock.quantity, Decimal('8.00'))

    def test_sales_order_deliver_endpoint(self):
        models.StockLevel.objects.filter(
            tenant=self.tenant,
            warehouse=self.warehouse,
            product=self.finished,
        ).update(quantity=Decimal('10.00'))
        so = models.SalesOrder.objects.create(
            tenant=self.tenant,
            so_number='SO-1',
            customer=self.customer,
            order_date='2026-01-01',
        )
        models.SalesOrderLine.objects.create(
            tenant=self.tenant,
            sales_order=so,
            product=self.finished,
            quantity=Decimal('4.00'),
            unit_price=Decimal('20.00'),
        )
        response = self.client.post('/sales-orders/%s/deliver/?tenant_id=%s' % (so.id, self.tenant.id), {
            'warehouse': self.warehouse.id,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        so.refresh_from_db()
        self.assertEqual(so.status, models.SalesOrder.DELIVERED)
        stock = models.StockLevel.objects.get(tenant=self.tenant, warehouse=self.warehouse, product=self.finished)
        self.assertEqual(stock.quantity, Decimal('6.00'))

    def test_manufacturing_output_endpoint(self):
        models.BillOfMaterial.objects.create(
            tenant=self.tenant,
            product=self.finished,
            component=self.component,
            quantity=Decimal('2.00'),
        )
        mo = models.ManufacturingOrder.objects.create(
            tenant=self.tenant,
            mo_number='MO-1',
            product=self.finished,
            quantity=Decimal('5.00'),
            status=models.ManufacturingOrder.IN_PROGRESS,
        )

        response = self.client.post('/manufacturing-orders/%s/record_output/?tenant_id=%s' % (mo.id, self.tenant.id), {
            'warehouse': self.warehouse.id,
            'output_quantity': '5.00',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        mo.refresh_from_db()
        self.assertEqual(mo.status, models.ManufacturingOrder.DONE)

        component_stock = models.StockLevel.objects.get(tenant=self.tenant, warehouse=self.warehouse, product=self.component)
        finished_stock = models.StockLevel.objects.get(tenant=self.tenant, warehouse=self.warehouse, product=self.finished)
        self.assertEqual(component_stock.quantity, Decimal('90.00'))
        self.assertEqual(finished_stock.quantity, Decimal('5.00'))

    def test_journal_post_inventory_endpoint(self):
        response = self.client.post('/journal-entries/post_inventory/?tenant_id=%s' % self.tenant.id, {
            'reference': 'INV-ADJ',
            'amount': '125.50',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.JournalLine.objects.filter(tenant=self.tenant).count(), 2)
