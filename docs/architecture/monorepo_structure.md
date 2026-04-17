# Monorepo Structure and Boundaries

```text
apps/
  api/            # DRF/Ninja HTTP API service
  worker/         # Celery workers
  admin_portal/   # Django admin focused operations UI
  pos_backend/    # POS-focused API facade if split from main api app
  docs/           # doc tooling (mkdocs/sphinx)
services/
  config/         # settings bootstrap + env parsing
  common/         # shared primitives only (clock, IDs, exceptions)
  audit/          # audit writer and diffing
  events/         # outbox + publisher
  permissions/    # role checks + scope resolution
  money/          # Money value object + rounding policies
  taxation/       # tax rules/calculation services
  inventory_engine/ # ledger posting + reservation algorithms
  posting_engine/ # finance posting intents -> journals
  pricing_engine/ # price list, promo, discount engine
  idempotency/    # idempotent write guards
  testing/        # factory helpers, fixtures, builders
django_apps/
  iam/
  tenancy/
  master_data/
  inventory/
  procurement/
  manufacturing/
  sales/
  pos/
  finance/
  reporting/
  notifications/
  files/
  workflow/
infra/
  docker/
  k8s/
  terraform/
  monitoring/
  scripts/
docs/
  adr/
  architecture/
  api/
  runbooks/
```

## Coupling rules
- `django_apps/*` may depend on `services/*`; inverse is forbidden except typed interfaces.
- `services/common` cannot import domain apps; keep it primitive.
- API controllers call application services; they must not embed business invariants.
- Domain invariants live in services/use-cases + model methods with transaction guards.
