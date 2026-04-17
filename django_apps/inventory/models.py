from __future__ import annotations

import uuid
from django.db import models


class InventoryTxnType(models.TextChoices):
    PURCHASE_RECEIPT = "purchase_receipt", "Purchase Receipt"
    SALES_ISSUE = "sales_issue", "Sales Issue"
    PRODUCTION_ISSUE = "production_issue", "Production Issue"
    PRODUCTION_OUTPUT = "production_output", "Production Output"
    ADJUSTMENT = "adjustment", "Adjustment"
    TRANSFER_OUT = "transfer_out", "Transfer Out"
    TRANSFER_IN = "transfer_in", "Transfer In"


class StockLedgerEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.UUIDField(db_index=True)
    item_id = models.UUIDField(db_index=True)
    warehouse_id = models.UUIDField(db_index=True)
    location_id = models.UUIDField(null=True, blank=True, db_index=True)
    lot_batch_id = models.UUIDField(null=True, blank=True)
    serial_number_id = models.UUIDField(null=True, blank=True)
    txn_type = models.CharField(max_length=40, choices=InventoryTxnType.choices)
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    uom = models.CharField(max_length=16)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    source_doc_type = models.CharField(max_length=40)
    source_doc_id = models.UUIDField()
    posted_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_stock_ledger_entry"
        indexes = [
            models.Index(fields=["company_id", "item_id", "warehouse_id", "posted_at"]),
            models.Index(fields=["source_doc_type", "source_doc_id"]),
        ]


class StockBalance(models.Model):
    company_id = models.UUIDField(db_index=True)
    item_id = models.UUIDField(db_index=True)
    warehouse_id = models.UUIDField(db_index=True)
    location_id = models.UUIDField(null=True, blank=True)
    lot_batch_id = models.UUIDField(null=True, blank=True)
    serial_number_id = models.UUIDField(null=True, blank=True)
    qty_on_hand = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    qty_reserved = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_stock_balance"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "company_id",
                    "item_id",
                    "warehouse_id",
                    "location_id",
                    "lot_batch_id",
                    "serial_number_id",
                ],
                name="uq_stock_balance_dim",
            )
        ]
