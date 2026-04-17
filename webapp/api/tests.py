# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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

    def test_missing_tenant_returns_empty(self):
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
