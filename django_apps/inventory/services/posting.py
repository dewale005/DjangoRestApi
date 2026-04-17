from __future__ import annotations

from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from django_apps.inventory.models import StockBalance, StockLedgerEntry


class InsufficientStockError(Exception):
    pass


class InventoryPostingService:
    """Posts immutable ledger rows and projects StockBalance with locking."""

    @staticmethod
    @transaction.atomic
    def post_issue(*, company_id, item_id, warehouse_id, qty: Decimal, source_doc_type: str, source_doc_id):
        balance = (
            StockBalance.objects.select_for_update()
            .filter(company_id=company_id, item_id=item_id, warehouse_id=warehouse_id)
            .first()
        )
        if balance is None or balance.qty_on_hand - balance.qty_reserved < qty:
            raise InsufficientStockError("negative stock blocked")

        balance.qty_on_hand = balance.qty_on_hand - qty
        balance.save(update_fields=["qty_on_hand", "updated_at"])

        StockLedgerEntry.objects.create(
            company_id=company_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            txn_type="sales_issue",
            quantity=-qty,
            uom="EA",
            source_doc_type=source_doc_type,
            source_doc_id=source_doc_id,
            posted_at=timezone.now(),
        )
