# Schema Catalog (High-write ERP/POS)

## Conventions
- Every transactional table has: `id (uuid)`, `company_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `version`.
- Soft delete: `is_deleted` + `deleted_at` + `deleted_by` for master data only.
- Append-only tables (ledger/journal/audit/outbox) are immutable, no soft delete.
- All monetary fields use `Decimal(18,6)` + currency code.

## Selected critical tables

| Table | Model | Purpose | Constraints / Indexes |
|---|---|---|---|
| `tenancy_company` | `Company` | tenant/legal entity | unique(`code`), idx(`status`) |
| `iam_role_assignment` | `RoleAssignment` | user role in scope | unique(`user`,`company`,`role`,`scope_type`,`scope_id`) |
| `master_product` | `Product` | product template | unique(`company`,`sku`), idx(`type`,`status`) |
| `master_product_variant` | `ProductVariant` | sellable/manufacturable item | unique(`company`,`product`,`variant_code`) |
| `inventory_stock_ledger_entry` | `StockLedgerEntry` | immutable stock movement source-of-truth | idx(`company`,`item`,`warehouse`,`posted_at`), idx(`source_doc_type`,`source_doc_id`) |
| `inventory_stock_balance` | `StockBalance` | current qty projection by location/lot | unique(`company`,`item`,`warehouse`,`location`,`lot`,`serial`) |
| `inventory_stock_reservation` | `StockReservation` | reserved qty for order/mo | idx(`status`,`expires_at`) |
| `procurement_purchase_order` | `PurchaseOrder` | supplier purchase contract | unique(`company`,`po_number`) |
| `manufacturing_mo` | `ManufacturingOrder` | production execution order | unique(`company`,`mo_number`), idx(`status`,`planned_start`) |
| `pos_sale` | `PosSale` | POS transaction | unique(`company`,`store`,`terminal`,`device_txn_id`) |
| `finance_journal_entry` | `JournalEntry` | accounting entries | unique(`company`,`journal_no`) |
| `platform_idempotency_key` | `IdempotencyKey` | idempotent request guard | unique(`company`,`key`,`endpoint`) |
| `platform_outbox_event` | `OutboxEvent` | reliable event publish queue | idx(`status`,`available_at`) |

## Row-locking rules
- `inventory_stock_balance`: lock rows with `select_for_update` during checkout/issue/transfer.
- `number_sequence`: lock one row per doc-type/company to allocate immutable numbers.
- `pos_session` and `cash_drawer`: lock during close/reconcile.

## State machines
- Manufacturing order: `draft -> planned -> released -> in_progress -> partially_completed -> completed -> closed` with cancel path from pre-closed states.
- POS session: `pending_open -> open -> suspended -> closing -> closed -> reconciled`.
- POS sale: `draft_cart -> suspended -> finalized -> paid -> refunded_partial/refunded_full`.
