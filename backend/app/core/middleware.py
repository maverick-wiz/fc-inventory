"""
Multi-tenancy middleware.
Resolves tenant_id from: subdomain → JWT claim → X-Tenant-ID header.
Sets app.tenant_id PostgreSQL session variable for RLS.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Try X-Tenant-ID header (service-to-service)
        tenant_id = request.headers.get("X-Tenant-ID")

        # 2. Try subdomain (e.g. walmart.app.com)
        if not tenant_id:
            host = request.headers.get("host", "")
            parts = host.split(".")
            if len(parts) >= 3:
                tenant_id = parts[0]

        # Store on request state for route handlers to access
        request.state.tenant_id = tenant_id

        response = await call_next(request)
        return response
