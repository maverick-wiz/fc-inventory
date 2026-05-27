# FC-Inventory 📦

**Multi-Tenant Retail Inventory Application**

> Tenants: Walmart · Target · Loblaws · Best Buy

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python FastAPI (async) |
| Database | PostgreSQL 16+ (Row-Level Security) |
| Cache / Broker | Redis 8 |
| Async Workers | Celery + Celery Beat |
| API Spec | OpenAPI 3.1 / Swagger |
| Container | Docker + Kubernetes (EKS/GKE/AKS) |
| GitOps | ArgoCD + Helm |
| CI/CD | GitHub Actions |

## Quick Start

```bash
# Clone
git clone https://github.com/maverick-wiz/fc-inventory.git
cd fc-inventory

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

## Project Structure

```
fc-inventory/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/v1/       # Route handlers + Pydantic schemas
│   │   ├── core/         # Config, security, middleware
│   │   ├── db/           # SQLAlchemy models + Alembic migrations
│   │   ├── services/     # Business logic layer
│   │   └── workers/      # Celery tasks
│   └── tests/            # pytest unit + integration
├── frontend/             # React SPA
│   └── src/
│       ├── components/   # Shared UI components
│       ├── pages/        # Route-level pages
│       ├── hooks/        # Custom React hooks
│       └── api/          # Axios API client
├── helm/                 # Helm chart for K8s deployment
├── k8s/                  # Kustomize overlays (dev/staging/prod)
├── .github/workflows/    # GitHub Actions CI/CD
├── docs/                 # Architecture + ERD documentation
└── scripts/              # Seed data + utility scripts
```

## Jira Integration

All commits and PRs must reference a Jira ticket:
```
git commit -m "SCRUM-XX: description of change"
```

Ticket transitions triggered automatically:
- PR opened → ticket moves to **In Review**
- PR approved → comment posted on ticket
- PR merged → ticket moves to **Done**

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready code. Protected. Requires PR + approval. |
| `develop` | Integration branch. PRs target here first. |
| `feature/SCRUM-XX-description` | Feature branches per Jira ticket |
| `fix/SCRUM-XX-description` | Bug fix branches |
| `hotfix/SCRUM-XX-description` | Production hotfixes |

## Team

| Agent | Role | Jira Epic |
|---|---|---|
| Maverick | Tech Lead | — |
| ALPHA | DevOps Architect | SCRUM-32 |
| OMEGA | Lead Coder | SCRUM-53 |
| SHADOW | Security Architect | SCRUM-52 |
| DELTA | QA Lead | SCRUM-51 |

---
*Maintained by Team Maverick — coordinated by Hermes AI*
