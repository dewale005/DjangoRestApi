# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from webapp.api import models

admin.site.register(models.Tenant)
admin.site.register(models.Partner)
admin.site.register(models.Warehouse)
admin.site.register(models.ProductCategory)
admin.site.register(models.Product)
admin.site.register(models.StockLevel)
admin.site.register(models.StockMovement)
admin.site.register(models.PurchaseOrder)
admin.site.register(models.PurchaseOrderLine)
admin.site.register(models.SalesOrder)
admin.site.register(models.SalesOrderLine)
admin.site.register(models.BillOfMaterial)
admin.site.register(models.ManufacturingOrder)
admin.site.register(models.Employee)
admin.site.register(models.PayrollEntry)
admin.site.register(models.Account)
admin.site.register(models.JournalEntry)
admin.site.register(models.JournalLine)
admin.site.register(models.Lead)
