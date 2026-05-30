"""
FastAPI dependency injectors: get_current_user, require_role, get_tenant_id.
"""
from typing import Annotated, List
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from app.core.redis import get_redis
import redis.asyncio as aioredis

bearer_scheme = HTTPBearer(auto_error=False)


async def get_tenant_id(request: Request) -> str:
    """Resolve tenant_id from middleware-set state."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant could not be resolved")
    return tenant_id


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> dict:
    """Validate JWT and return payload. Check JTI blocklist in Redis."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    jti = payload.get("jti")
    if jti and await redis.get(f"blocklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    return payload


def require_role(roles: List[str]):
    """Role gate dependency factory."""
    async def _check(current_user: Annotated[dict, Depends(get_current_user)]):
        user_role = current_user.get("role", "read_only")
        role_hierarchy = ["read_only", "warehouse_op", "store_manager", "tenant_admin"]
        min_level = min((role_hierarchy.index(r) for r in roles if r in role_hierarchy), default=99)
        user_level = role_hierarchy.index(user_role) if user_role in role_hierarchy else -1
        if user_level < min_level:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return _check
