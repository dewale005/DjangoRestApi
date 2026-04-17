from __future__ import annotations

from django.db import transaction

from django_apps.inventory.services.posting import InventoryPostingService


class PosCheckoutService:
    @staticmethod
    @transaction.atomic
    def checkout(*, company_id, sale, lines):
        # price/tax validation omitted in scaffold
        for line in lines:
            InventoryPostingService.post_issue(
                company_id=company_id,
                item_id=line["item_id"],
                warehouse_id=line["warehouse_id"],
                qty=line["qty"],
                source_doc_type="pos_sale",
                source_doc_id=sale.id,
            )
        # create payments/journal intents/outbox in same transaction
        return sale
