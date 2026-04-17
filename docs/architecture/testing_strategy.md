# Testing Strategy

## Tooling
- pytest, pytest-django, pytest-xdist
- factory_boy, faker, freezegun
- testcontainers for PostgreSQL/Redis in integration and e2e suites

## Suites
- Unit: `tests/unit/**`
- Integration: `tests/integration/**`
- E2E/API: `tests/e2e/**`

## Example high-value tests
- `test_negative_stock_blocked_when_config_disabled`
- `test_pos_checkout_idempotent_replay_returns_same_sale`
- `test_mo_issue_materials_updates_ledger_and_reservations`
- `test_outbox_event_persisted_in_same_transaction`
- `test_concurrent_checkout_locking_prevents_double_deduct`

## CI thresholds
- Unit coverage >= 85%
- Integration critical path coverage >= 75%
- Zero flaky tests policy with retry disabled by default
