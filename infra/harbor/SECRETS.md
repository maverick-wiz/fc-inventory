# Harbor GitHub Secrets Required

Add these secrets to your GitHub repository under:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | Notes |
|---|---|---|
| `HARBOR_URL` | `harbor.local:30080` | Harbor NodePort URL |
| `HARBOR_USERNAME` | `robot$backend-ci-v2` | Backend CI robot account |
| `HARBOR_PASSWORD` | *(see /tmp/backend-robot-secret.txt on Azure VM)* | Robot account token |

## Frontend Image Secrets (optional separate robot)
| `HARBOR_FRONTEND_USERNAME` | `robot$frontend-ci-v2` | Frontend CI robot account |
| `HARBOR_FRONTEND_PASSWORD` | *(see /tmp/frontend-robot-secret.txt on Azure VM)* | Robot account token |

## Harbor Admin (do NOT use in CI)
- Admin user: `admin`
- Admin password: stored in Vault / team password manager
- **Never commit Harbor credentials to source code**

## Note on Production
In production (AWS/GCP), replace Harbor secrets with:
- ECR: use OIDC + IAM role (no static credentials needed)
- GCR: use Workload Identity Federation

## Trivy Integration
Harbor automatically scans every pushed image with Trivy.
- Images with CRITICAL vulnerabilities will be blocked from pull.
- View scan results: http://harbor.local:30080 → Projects → fc-inventory-backend → Repositories
# Harbor: admin credentials used for CI push (all-project access)
