# Deployment Runbook

## Local
- `docker compose -f infra/docker/docker-compose.yml up --build`

## Staging/Production
1. Build/push images (`api`, `worker`, `beat`).
2. Apply migrations as pre-deploy job.
3. Deploy app with rolling update (`maxUnavailable=0`).
4. Run smoke tests and readiness checks.

## Rollback
- Roll back deployment image tag.
- If migration is non-reversible, use expand/contract migration pattern.

## Backups
- PostgreSQL PITR enabled.
- Redis persistence optional; outbox and idempotency are DB backed.
