# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from webapp.api import models


class InventoryService(object):

    @staticmethod
    @transaction.atomic
    def adjust_stock(tenant_id, warehouse_id, product_id, quantity_delta, reference, notes):
        quantity_delta = Decimal(str(quantity_delta))
        tenant = models.Tenant.objects.get(id=tenant_id)
        stock_level = models.StockLevel.objects.select_for_update().filter(
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
        ).first()
        if not stock_level:
            stock_level = models.StockLevel.objects.create(
                tenant_id=tenant_id,
                warehouse_id=warehouse_id,
                product_id=product_id,
                quantity=Decimal('0.00'),
            )

        new_qty = stock_level.quantity + quantity_delta
        if (not tenant.allow_negative_stock) and new_qty < 0:
            raise ValidationError('Stock adjustment would result in negative stock.')

        stock_level.quantity = new_qty
        stock_level.save(update_fields=['quantity'])

        movement_type = models.StockMovement.IN if quantity_delta >= 0 else models.StockMovement.OUT
        models.StockMovement.objects.create(
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            quantity=abs(quantity_delta),
            reference=reference,
            notes=notes,
        )
        return stock_level


class ProcurementService(object):

    @staticmethod
    @transaction.atomic
    def receive_purchase_order(tenant_id, purchase_order_id, warehouse_id):
        purchase_order = models.PurchaseOrder.objects.select_for_update().get(
            id=purchase_order_id,
            tenant_id=tenant_id,
        )
        if purchase_order.status == models.PurchaseOrder.RECEIVED:
            raise ValidationError('Purchase order already received.')

        lines = purchase_order.lines.select_related('product').all()
        if not lines:
            raise ValidationError('Purchase order does not contain lines.')

        for line in lines:
            InventoryService.adjust_stock(
                tenant_id=tenant_id,
                warehouse_id=warehouse_id,
                product_id=line.product_id,
                quantity_delta=line.quantity,
                reference=purchase_order.po_number,
                notes='PO receipt',
            )

        purchase_order.status = models.PurchaseOrder.RECEIVED
        purchase_order.save(update_fields=['status'])

        OutboxService.record_event(
            tenant_id=tenant_id,
            aggregate_type='purchase_order',
            aggregate_id=purchase_order.id,
            event_type='procurement.purchase_order.received',
            payload={'purchase_order_id': purchase_order.id, 'warehouse_id': warehouse_id},
        )
        return purchase_order


class SalesService(object):

    @staticmethod
    @transaction.atomic
    def deliver_sales_order(tenant_id, sales_order_id, warehouse_id):
        sales_order = models.SalesOrder.objects.select_for_update().get(id=sales_order_id, tenant_id=tenant_id)
        if sales_order.status == models.SalesOrder.DELIVERED:
            raise ValidationError('Sales order already delivered.')

        lines = sales_order.lines.select_related('product').all()
        if not lines:
            raise ValidationError('Sales order does not contain lines.')

        for line in lines:
            InventoryService.adjust_stock(
                tenant_id=tenant_id,
                warehouse_id=warehouse_id,
                product_id=line.product_id,
                quantity_delta=Decimal('0.00') - line.quantity,
                reference=sales_order.so_number,
                notes='Sales order delivery',
            )

        sales_order.status = models.SalesOrder.DELIVERED
        sales_order.save(update_fields=['status'])

        OutboxService.record_event(
            tenant_id=tenant_id,
            aggregate_type='sales_order',
            aggregate_id=sales_order.id,
            event_type='sales.sales_order.delivered',
            payload={'sales_order_id': sales_order.id, 'warehouse_id': warehouse_id},
        )
        return sales_order


class ManufacturingService(object):

    @staticmethod
    @transaction.atomic
    def record_output(tenant_id, manufacturing_order_id, warehouse_id, output_quantity):
        manufacturing_order = models.ManufacturingOrder.objects.select_for_update().get(
            id=manufacturing_order_id,
            tenant_id=tenant_id,
        )
        output_quantity = Decimal(str(output_quantity))
        if output_quantity <= 0:
            raise ValidationError('Output quantity should be greater than zero.')

        bom_lines = models.BillOfMaterial.objects.filter(
            tenant_id=tenant_id,
            product_id=manufacturing_order.product_id,
        )
        for bom_line in bom_lines:
            required_component_qty = bom_line.quantity * output_quantity
            InventoryService.adjust_stock(
                tenant_id=tenant_id,
                warehouse_id=warehouse_id,
                product_id=bom_line.component_id,
                quantity_delta=Decimal('0.00') - required_component_qty,
                reference=manufacturing_order.mo_number,
                notes='Manufacturing component consumption',
            )

        InventoryService.adjust_stock(
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            product_id=manufacturing_order.product_id,
            quantity_delta=output_quantity,
            reference=manufacturing_order.mo_number,
            notes='Manufacturing output',
        )

        manufacturing_order.status = models.ManufacturingOrder.DONE
        manufacturing_order.save(update_fields=['status'])

        OutboxService.record_event(
            tenant_id=tenant_id,
            aggregate_type='manufacturing_order',
            aggregate_id=manufacturing_order.id,
            event_type='manufacturing.output.recorded',
            payload={'manufacturing_order_id': manufacturing_order.id, 'output_quantity': str(output_quantity)},
        )
        return manufacturing_order


class FinanceService(object):

    @staticmethod
    @transaction.atomic
    def post_inventory_adjustment_journal(tenant_id, reference, amount):
        amount = Decimal(str(amount))
        entry = models.JournalEntry.objects.create(
            tenant_id=tenant_id,
            entry_number='JE-%s' % uuid.uuid4().hex[:10].upper(),
            description='Auto posting for %s' % reference,
            posted_on=timezone.now().date(),
        )
        debit_account = models.Account.objects.filter(tenant_id=tenant_id).order_by('id').first()
        credit_account = models.Account.objects.filter(tenant_id=tenant_id).order_by('-id').first()
        if not debit_account or not credit_account:
            raise ValidationError('At least two accounts are required for journal posting.')

        models.JournalLine.objects.create(
            tenant_id=tenant_id,
            journal_entry=entry,
            account=debit_account,
            debit=amount,
            credit=Decimal('0.00'),
        )
        models.JournalLine.objects.create(
            tenant_id=tenant_id,
            journal_entry=entry,
            account=credit_account,
            debit=Decimal('0.00'),
            credit=amount,
        )
        return entry


class OutboxService(object):

    @staticmethod
    def record_event(tenant_id, aggregate_type, aggregate_id, event_type, payload):
        models.OutboxEvent.objects.create(
            tenant_id=tenant_id,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            event_type=event_type,
            payload=json.dumps(payload),
            status=models.OutboxEvent.PENDING,
        )


class PosService(object):

    @staticmethod
    @transaction.atomic
    def open_session(tenant_id, terminal_id, opening_float):
        terminal = models.PosTerminal.objects.get(id=terminal_id, tenant_id=tenant_id, is_active=True)
        existing_open = models.PosSession.objects.filter(
            tenant_id=tenant_id,
            terminal=terminal,
            status=models.PosSession.OPEN,
        ).first()
        if existing_open:
            raise ValidationError('Terminal already has an open session.')

        session = models.PosSession.objects.create(
            tenant_id=tenant_id,
            terminal=terminal,
            status=models.PosSession.OPEN,
            opened_at=timezone.now(),
            opening_float=opening_float,
        )
        return session

    @staticmethod
    @transaction.atomic
    def checkout(tenant_id, session_id, idempotency_key, lines, payments, customer_id=None):
        existing = models.PosSale.objects.filter(tenant_id=tenant_id, idempotency_key=idempotency_key).first()
        if existing:
            return existing, True

        session = models.PosSession.objects.select_for_update().get(id=session_id, tenant_id=tenant_id)
        if session.status != models.PosSession.OPEN:
            raise ValidationError('Session is not open.')

        sale = models.PosSale.objects.create(
            tenant_id=tenant_id,
            session=session,
            customer_id=customer_id,
            idempotency_key=idempotency_key,
            sale_number='POS-%s' % uuid.uuid4().hex[:10].upper(),
            status=models.PosSale.PAID,
        )

        subtotal = Decimal('0.00')
        tax_total = Decimal('0.00')

        for line in lines:
            quantity = Decimal(str(line['quantity']))
            unit_price = Decimal(str(line['unit_price']))
            tax_amount = Decimal(str(line.get('tax_amount', '0.00')))
            line_total = quantity * unit_price + tax_amount
            subtotal += quantity * unit_price
            tax_total += tax_amount

            InventoryService.adjust_stock(
                tenant_id=tenant_id,
                warehouse_id=line['warehouse'],
                product_id=line['product'],
                quantity_delta=Decimal('0.00') - quantity,
                reference=sale.sale_number,
                notes='POS checkout',
            )

            models.PosSaleLine.objects.create(
                tenant_id=tenant_id,
                sale=sale,
                product_id=line['product'],
                warehouse_id=line['warehouse'],
                quantity=quantity,
                unit_price=unit_price,
                tax_amount=tax_amount,
                line_total=line_total,
            )

        payments_total = Decimal('0.00')
        for payment in payments:
            amount = Decimal(str(payment['amount']))
            payments_total += amount
            models.PosPayment.objects.create(
                tenant_id=tenant_id,
                sale=sale,
                payment_method=payment['payment_method'],
                amount=amount,
                reference=payment.get('reference', ''),
            )

        total_amount = subtotal + tax_total
        if payments_total < total_amount:
            raise ValidationError('Payments do not cover total amount.')

        sale.subtotal = subtotal
        sale.tax_total = tax_total
        sale.total_amount = total_amount
        sale.save(update_fields=['subtotal', 'tax_total', 'total_amount'])

        response_payload = {
            'sale_id': sale.id,
            'sale_number': sale.sale_number,
            'total_amount': str(sale.total_amount),
        }
        models.IdempotencyKey.objects.create(
            tenant_id=tenant_id,
            key=idempotency_key,
            endpoint='pos.checkout',
            status_code=201,
            response_payload=json.dumps(response_payload),
        )
        OutboxService.record_event(
            tenant_id=tenant_id,
            aggregate_type='pos_sale',
            aggregate_id=sale.id,
            event_type='pos.sale.created',
            payload=response_payload,
        )
        return sale, False

    @staticmethod
    @transaction.atomic
    def refund(tenant_id, sale_id, amount):
        sale = models.PosSale.objects.select_for_update().get(id=sale_id, tenant_id=tenant_id)
        refund_amount = Decimal(str(amount))
        if refund_amount <= 0:
            raise ValidationError('Refund amount should be greater than zero.')
        if sale.refunded_amount + refund_amount > sale.total_amount:
            raise ValidationError('Refund exceeds sale amount.')

        for line in sale.lines.all():
            InventoryService.adjust_stock(
                tenant_id=tenant_id,
                warehouse_id=line.warehouse_id,
                product_id=line.product_id,
                quantity_delta=line.quantity,
                reference=sale.sale_number,
                notes='POS refund',
            )

        sale.refunded_amount = sale.refunded_amount + refund_amount
        if sale.refunded_amount == sale.total_amount:
            sale.status = models.PosSale.REFUNDED_FULL
        else:
            sale.status = models.PosSale.REFUNDED_PARTIAL
        sale.save(update_fields=['refunded_amount', 'status'])

        OutboxService.record_event(
            tenant_id=tenant_id,
            aggregate_type='pos_sale',
            aggregate_id=sale.id,
            event_type='pos.sale.refunded',
            payload={'sale_id': sale.id, 'refund_amount': str(refund_amount)},
        )
        return sale
