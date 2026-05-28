# ADR-005: Harbor as Container Registry for FC-Inventory

**Date:** 2025-05-28
**Status:** Accepted
**Deciders:** Maverick (Tech Lead), ALPHA (DevOps Architect)
**Jira Epic:** FCINV-233

---

## Context

FC-Inventory requires a container registry to store Docker images built by GitHub Actions CI/CD pipelines. Images need to be:
- Built on every push to `main` and `develop`
- Vulnerability scanned before deployment
- Access-controlled per service (backend vs frontend vs celery-worker)
- Pullable by Kubernetes pods in `production` and `staging` namespaces
- Migratable to cloud registries (ECR/GCR) when moving to production

The registry must be **open-source**, **self-hosted**, and deployable on the existing minikube-test cluster.

---

## Decision

Deploy **Harbor v2.15.1** (CNCF Graduated project) as the self-hosted container registry via the official `harbor/harbor` Helm chart.

**Deployed at:** `http://harbor.local:30080`
**Namespace:** `harbor` on minikube-test

---

## Alternatives Considered

| Option | CNCF Status | Vuln Scanning | K8s Helm Chart | Multi-tenant RBAC | Verdict |
|---|---|---|---|---|---|
| **Harbor** ✅ | Graduated | Trivy (built-in) | ✅ Official | Projects + Robot Accounts | **Selected** |
| Docker Registry v2 | Not a member | ❌ None | Manual | ❌ None | Rejected — no scanning, no RBAC |
| Nexus OSS | Not a member | ❌ None | Complex | Limited | Rejected — heavy, complex config |
| Zot | Sandbox | Limited | Manual | Limited | Rejected — immature, no RBAC |
| AWS ECR | N/A (AWS) | ✅ (paid) | N/A | IAM-based | Not applicable for on-prem dev |

---

## Implementation

### Infrastructure
- Deployed via `harbor/harbor` Helm chart v1.19.1 (Harbor v2.15.1)
- NodePort 30080 → `harbor.local` via `/etc/hosts` mapping
- Internal PostgreSQL + Redis (Harbor manages its own for simplicity in dev)
- TLS disabled in dev (self-signed cert required for production)
- 10Gi PVC for registry storage (minikube `standard` StorageClass)

### Projects Created
| Project | Access | Robot Account | Scan Policy |
|---|---|---|---|
| `fc-inventory-backend` | Private | `robot$backend-ci-v2` | Scan on push, block CRITICAL |
| `fc-inventory-frontend` | Private | `robot$frontend-ci-v2` | Scan on push, block CRITICAL |

### GitHub Actions Integration
- Job `docker-build-push` in `.github/workflows/ci.yml`
- Triggers on push to `main` after backend + frontend tests pass
- Uses `docker/login-action@v3` + `docker/build-push-action@v5`
- Image tags: `harbor.local:30080/<project>/app:<git-sha>` and `:latest`
- Build cache via GitHub Actions cache (GHA backend)

### Kubernetes Integration
- `harbor-pull-secret` (dockerconfigjson) created in `production` and `staging` namespaces
- Default service accounts patched with imagePullSecrets
- Robot account credentials stored as K8s secrets (not in source code)

---

## Consequences

### Positive
- ✅ Native Trivy integration — every image scanned automatically, zero config overhead
- ✅ Project-based RBAC maps cleanly to backend/frontend/worker service split
- ✅ `harbor/harbor` Helm chart deploys in <10 minutes on minikube
- ✅ Image replication to ECR/GCR available when going to production (zero rework)
- ✅ Open source, no licensing cost
- ✅ Web UI for image management and vulnerability reports at http://harbor.local:30080

### Negative
- ⚠️ Requires `insecure-registries` in Docker daemon config (dev only — TLS disabled)
- ⚠️ Harbor NodePort is not internet-accessible — GitHub Actions runners cannot push directly; requires self-hosted runners or a tunnel (ngrok/cloudflare) for true CI push
- ⚠️ Additional 10Gi storage consumption on minikube
- ⚠️ Harbor admin password must be rotated and stored in Vault (production requirement)
- ⚠️ Internal Harbor DB/Redis = not HA; for production, externalise to managed PostgreSQL + Redis

---

## Production Alternative

When FC-Inventory moves to AWS:
- **ECR (Elastic Container Registry)** per service + OIDC Workload Identity (no static creds)
- Harbor remains for on-prem / air-gapped / private cloud deployments
- Image replication from Harbor → ECR can be configured in Harbor's replication policy UI

---

## Security Analysis (STRIDE)

| Threat | Mitigation |
|---|---|
| **S** Spoofing | Robot accounts scoped per project; admin account restricted |
| **T** Tampering | Image digests enforced; Trivy blocks vulnerable images |
| **R** Repudiation | Harbor audit log enabled; all push/pull events recorded |
| **I** Disclosure | All projects set to Private; no anonymous access |
| **D** Denial of Service | Resource limits on Harbor pods; 10Gi registry PVC with quota |
| **E** Elevation of Privilege | Robot accounts have minimum permissions (push+pull only, no admin) |

---

## References
- Harbor CNCF project: https://goharbor.io/
- Helm chart: https://github.com/goharbor/harbor-helm
- Trivy integration docs: https://goharbor.io/docs/latest/administration/vulnerability-scanning/
- FCINV-233 epic: https://wizkidtester.atlassian.net/browse/FCINV-233
