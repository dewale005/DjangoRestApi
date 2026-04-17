# ERP + POS Architecture Blueprint (Production-Grade, Django Modular Monolith)

## 1) Assumptions
- Target runtime: Python 3.12+, Django 5.x, PostgreSQL 16, Redis 7, Celery 5.
- Monorepo starts as modular monolith; bounded contexts separated as Django apps and service packages.
- OLTP DB: PostgreSQL only (no SQLite in CI/prod).
- Strong consistency required for inventory, POS checkout, and finance posting triggers.
- Eventual consistency accepted for reporting projections and notifications.
- Tenancy model: user belongs to one or more companies, with scoped roles per company/store/warehouse.
- Numbering strategy: immutable sequence per company + document type + fiscal year.
- Stock ledger is append-only; stock balances are projection tables with reconciliation jobs.

## 2) Architecture Summary
- **Ingress/API**: DRF API app with JWT authentication and RBAC enforcement.
- **Domain layer**: django apps (iam, tenancy, inventory, procurement, manufacturing, sales, pos, finance).
- **Application layer**: orchestrating services in `services/*_engine` and context-specific use-cases.
- **Async layer**: transactional outbox table + Celery workers for reliable publish/process.
- **Persistence**: PostgreSQL + selective row-level locking (`select_for_update`) on inventory and numbering rows.
- **Observability**: OpenTelemetry traces, Prometheus metrics, structured logs with correlation IDs.

## 3) Monorepo Structure
See `/docs/architecture/monorepo_structure.md` for tree and ownership boundaries.

## 4) Backend Module Design (Bounded Contexts)
- **iam**: users, roles, permission grants, refresh token revocation.
- **tenancy**: companies, branches, legal entities, feature flags.
- **master_data**: products, variants, UOM, barcodes, prices, tax profiles, customers, suppliers.
- **inventory**: stock ledger entries, balances, lots/serials, reservations, transfers, adjustments, cycle counts.
- **procurement**: requisitions, RFQs, POs, goods receipts, supplier invoices, returns to supplier.
- **manufacturing**: BOM versioning, routings, production plans, MRP results, MOs, issue/output/scrap/quality.
- **sales**: quotations, sales orders, deliveries, invoices, returns, credit notes.
- **pos**: terminals, sessions, carts/sales, split payments, refunds/exchanges, cashier reconciliation.
- **finance**: chart of accounts, posting rules, journal entries, payment records, reconciliation hooks.
- **reporting**: async projection tables/materialized views for BI queries.
- **notifications/files/workflow**: attachments, approvals, event-driven notifications.

## 5) Database Schema (Core tables)
Detailed schema with constraints and indexes is captured in `/docs/architecture/schema_catalog.md` including:
- companies, users, roles, role_assignments
- stores, warehouses, warehouse_locations
- products, product_variants, product_barcodes, product_prices, product_costs
- inventory_items, stock_ledger_entries, stock_balances, stock_reservations, lot_batches, serial_numbers
- purchase_orders, goods_receipts, supplier_invoices
- bom_headers, bom_lines, routing_headers, routing_steps
- production_plans, manufacturing_orders, mo_materials, mo_operations, production_outputs, production_scrap
- sales_orders, deliveries, sales_invoices
- pos_terminals, pos_sessions, pos_sales, pos_sale_lines, pos_payments, pos_refunds, cash_drawer_movements
- chart_of_accounts, journal_entries, journal_entry_lines, payment_records
- audit_logs, idempotency_keys, outbox_events

## 6) API Design
Detailed endpoint map and contracts in `/docs/api/endpoints.md`.
- Idempotent write endpoints require `Idempotency-Key` header.
- Error contract:
  - `code`, `message`, `details`, `correlation_id`, `retryable`, `field_errors`.
- Critical commands use dedicated action endpoints (`/approve/`, `/release/`, `/issue-materials/`, `/record-output/`, `/checkout/`, `/refund/`).

## 7) Testing Strategy
Detailed pyramid and executable examples in `/docs/architecture/testing_strategy.md`.
- Unit: pricing/tax/idempotency/state transitions.
- Integration: transaction integrity, lock behavior, outbox persistence, projection consistency.
- E2E: procure->receive->produce->sell->refund.

## 8) Deployment Kit
Detailed deployment kit in `/docs/runbooks/deployment.md`.
- Docker images: api, worker, beat.
- Compose for local and CI integration tests.
- Kubernetes overlays for dev/staging/prod.
- Migration runbook and zero-downtime strategy.

## 9) Delivery Roadmap
See `/docs/architecture/roadmap.md`.
- Phase 1: auth, tenancy, products, inventory ledger, PO/GRN, basic POS checkout.
- Phase 2: BOM/MO + issue/output + journal framework.
- Phase 3: advanced POS, loyalty/promotions, transfers, returns/refunds, approvals.
- Phase 4: MRP, forecasting hooks, advanced finance, analytics, external integrations.
