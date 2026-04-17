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
