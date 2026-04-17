# DjangoRestApi - Multi-Tenant ERP Inventory API

This project now includes a multi-tenant ERP backend built with Django + Django REST Framework.

## Implemented modules

- Tenant management
- CRM (Leads, Partners for customers/vendors)
- Inventory (Warehouses, Categories, Products, Stock Levels, Stock Movements)
- Purchasing (Purchase Orders + lines)
- Sales (Sales Orders + lines)
- Manufacturing (Bill of Materials, Manufacturing Orders)
- HR/Payroll (Employees, Payroll Entries)
- Accounting (Accounts, Journal Entries + lines)

## Multi-tenant behavior

All tenant-scoped endpoints require `tenant_id` as a query parameter for list access:

```
GET /products/?tenant_id=1
```

Create operations also enforce tenant scope and accept tenant from payload or query parameter.

## Main API endpoints

- `/tenants/`
- `/partners/`
- `/warehouses/`
- `/categories/`
- `/products/`
- `/stock-levels/`
- `/stock-movements/`
- `/purchase-orders/`
- `/purchase-order-lines/`
- `/sales-orders/`
- `/sales-order-lines/`
- `/bom/`
- `/manufacturing-orders/`
- `/employees/`
- `/payroll/`
- `/accounts/`
- `/journal-entries/`
- `/journal-lines/`
- `/leads/`

## Run locally

```bash
python manage.py makemigrations api
python manage.py migrate
python manage.py runserver
```


## DevOps / CI-CD

- CI workflow: `.github/workflows/ci.yml`
- CD workflow: `.github/workflows/cd.yml`
- Kubernetes manifests: `deploy/k8s/`
- Full deployment guide: `DEVOPS.md`


## ERP/POS Monorepo Blueprint

A production-ready ERP + POS architecture and scaffold has been added:
- Architecture blueprint: `docs/architecture/erp_pos_blueprint.md`
- Monorepo boundaries: `docs/architecture/monorepo_structure.md`
- Schema catalog: `docs/architecture/schema_catalog.md`
- API contracts: `docs/api/endpoints.md`
- Testing strategy: `docs/architecture/testing_strategy.md`
- Deployment runbook: `docs/runbooks/deployment.md`
- Delivery roadmap: `docs/architecture/roadmap.md`


## Working POS APIs

- Open POS session: `POST /pos/sessions/open/`
- Checkout sale: `POST /pos/sales/checkout/`
- Refund sale: `POST /pos-sales/{sale_id}/refund/?tenant_id={tenant_id}`

Checkout is idempotent using `idempotency_key` payload field (or `Idempotency-Key` header),
creates stock movements, updates stock levels with row locking, records payments,
and creates outbox events for async processing.
