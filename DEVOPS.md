# DevOps and Deployment Process

This repository now includes a complete CI/CD and multi-environment deployment pipeline.

## 1) Build and runtime

- `Dockerfile` builds a production-ready image with Gunicorn.
- `scripts/entrypoint.sh` runs DB migrations at startup before serving traffic.
- `.dockerignore` keeps images clean and smaller.

## 2) CI pipeline (`.github/workflows/ci.yml`)

Triggered on pull requests and pushes to `main`/`develop`.

Checks:
1. Install dependencies from `requirements.txt`
2. Validate migrations are committed (`makemigrations --check --dry-run`)
3. Execute Django tests
4. Validate Python syntax with `py_compile`
5. Build Docker image

## 3) CD pipeline (`.github/workflows/cd.yml`)

Triggered by:
- push to `develop` (auto deploy to dev)
- push to `main` (auto deploy to staging)
- semantic tags `v*` (promote to prod after staging)
- manual dispatch to `dev`/`staging`/`prod`

Flow:
1. Build and push image to `ghcr.io/<org>/<repo>:<sha>`
2. Deploy to selected Kubernetes environment via kustomize overlay
3. Wait for deployment rollout to finish

## 4) Environment strategy

- `development`: namespace `erp-dev`, 1 replica
- `staging`: namespace `erp-staging`, 2 replicas
- `production`: namespace `erp-prod`, 3 replicas

K8s manifests:
- Base: `deploy/k8s/base`
- Overlays: `deploy/k8s/overlays/{dev,staging,prod}`

## 5) Required GitHub secrets

- `KUBE_CONFIG_DEV` (base64 kubeconfig)
- `KUBE_CONFIG_STAGING` (base64 kubeconfig)
- `KUBE_CONFIG_PROD` (base64 kubeconfig)

## 6) Release process

1. Merge feature branch into `develop` for dev deploy.
2. Promote to `main` for staging validation.
3. Create tag like `v1.0.0` for production release.
4. Use GitHub Environment protection rules to require approvals for staging/prod.

## 7) Operational best practices

- Add branch protection for `main` and `develop`.
- Require CI checks before merge.
- Enable dependency scanning and secret scanning.
- Add alerting from Kubernetes metrics and logs.
- Rotate secrets periodically.
