"""
FC-Inventory — FastAPI Application Entry Point
SCRUM-62: OMEGA Onboarding 1 — Technical Architecture & Stack
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import TenantMiddleware
from app.api.v1.routes import auth, products, inventory, purchase_orders, calendar, reports, users, webhooks, warehouses, suppliers, audit

app = FastAPI(
    title="FC-Inventory API",
    description="Multi-Tenant Retail Inventory Application",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-tenancy middleware — resolves tenant_id from subdomain / JWT / X-Tenant-ID header
app.add_middleware(TenantMiddleware)

# Routers
app.include_router(auth.router,            prefix="/api/v1/auth",            tags=["Authentication"])
app.include_router(products.router,        prefix="/api/v1/products",        tags=["Products"])
app.include_router(inventory.router,       prefix="/api/v1/inventory",       tags=["Inventory"])
app.include_router(purchase_orders.router, prefix="/api/v1/purchase-orders", tags=["Purchase Orders"])
app.include_router(calendar.router,        prefix="/api/v1/calendar",        tags=["Calendar"])
app.include_router(reports.router,         prefix="/api/v1/reports",         tags=["Reports"])
app.include_router(users.router,           prefix="/api/v1/users",           tags=["Users"])
app.include_router(warehouses.router,      prefix="/api/v1/warehouses",      tags=["Warehouses"])
app.include_router(suppliers.router,       prefix="/api/v1/suppliers",       tags=["Suppliers"])
app.include_router(webhooks.router,        prefix="/api/v1/webhooks",        tags=["Webhooks"])
app.include_router(audit.router,           prefix="/api/v1/audit-logs",      tags=["Audit"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "fc-inventory-api", "version": "0.1.0"}


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "FC-Inventory API — see /api/docs"}
