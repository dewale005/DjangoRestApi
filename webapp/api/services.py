# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from webapp.api import models


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

        tenant = models.Tenant.objects.get(id=tenant_id)
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

            stock_level = models.StockLevel.objects.select_for_update().filter(
                tenant_id=tenant_id,
                warehouse_id=line['warehouse'],
                product_id=line['product'],
            ).first()
            available_qty = stock_level.quantity if stock_level else Decimal('0.00')

            if (not tenant.allow_negative_stock) and available_qty < quantity:
                raise ValidationError('Insufficient stock for product %s' % line['product'])

            if stock_level:
                stock_level.quantity = stock_level.quantity - quantity
                stock_level.save(update_fields=['quantity'])
            else:
                models.StockLevel.objects.create(
                    tenant_id=tenant_id,
                    warehouse_id=line['warehouse'],
                    product_id=line['product'],
                    quantity=Decimal('0.00') - quantity,
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
            models.StockMovement.objects.create(
                tenant_id=tenant_id,
                product_id=line['product'],
                warehouse_id=line['warehouse'],
                movement_type=models.StockMovement.OUT,
                quantity=quantity,
                reference=sale.sale_number,
                notes='POS checkout',
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
        models.OutboxEvent.objects.create(
            tenant_id=tenant_id,
            aggregate_type='pos_sale',
            aggregate_id=str(sale.id),
            event_type='pos.sale.created',
            payload=json.dumps(response_payload),
            status=models.OutboxEvent.PENDING,
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
            stock_level = models.StockLevel.objects.select_for_update().filter(
                tenant_id=tenant_id,
                warehouse=line.warehouse,
                product=line.product,
            ).first()
            if not stock_level:
                stock_level = models.StockLevel.objects.create(
                    tenant_id=tenant_id,
                    warehouse=line.warehouse,
                    product=line.product,
                    quantity=Decimal('0.00'),
                )
            stock_level.quantity = stock_level.quantity + line.quantity
            stock_level.save(update_fields=['quantity'])
            models.StockMovement.objects.create(
                tenant_id=tenant_id,
                product=line.product,
                warehouse=line.warehouse,
                movement_type=models.StockMovement.IN,
                quantity=line.quantity,
                reference=sale.sale_number,
                notes='POS refund',
            )

        sale.refunded_amount = sale.refunded_amount + refund_amount
        if sale.refunded_amount == sale.total_amount:
            sale.status = models.PosSale.REFUNDED_FULL
        else:
            sale.status = models.PosSale.REFUNDED_PARTIAL
        sale.save(update_fields=['refunded_amount', 'status'])
        return sale
