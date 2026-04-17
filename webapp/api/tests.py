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
