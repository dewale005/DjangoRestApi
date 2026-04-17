# API Endpoint Design (selected)

## Inventory
- `POST /api/inventory/adjustments/` (Idempotency-Key required)
- `POST /api/inventory/transfers/`
- `POST /api/inventory/transfers/{id}/ship/`
- `POST /api/inventory/transfers/{id}/receive/`

## Procurement
- `POST /api/purchase-orders/`
- `POST /api/purchase-orders/{id}/approve/`
- `POST /api/goods-receipts/`

## Manufacturing
- `POST /api/manufacturing-orders/`
- `POST /api/manufacturing-orders/{id}/release/`
- `POST /api/manufacturing-orders/{id}/issue-materials/`
- `POST /api/manufacturing-orders/{id}/record-output/`
- `POST /api/manufacturing-orders/{id}/record-scrap/`

## POS
- `POST /api/pos/sessions/open/`
- `POST /api/pos/sales/checkout/` (Idempotency-Key mandatory)
- `POST /api/pos/sales/{id}/refund/`
- `POST /api/pos/sales/{id}/exchange/`

## Error contract
```json
{
  "code": "inventory.negative_stock_blocked",
  "message": "Insufficient stock for item VAR-001",
  "details": {"available": "3.000", "requested": "5.000"},
  "correlation_id": "req-...",
  "retryable": false,
  "field_errors": {"lines[0].qty": ["Insufficient stock"]}
}
```
