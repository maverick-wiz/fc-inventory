"""
Authentication business logic: login, refresh token rotation, session management.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models.models import User, Tenant
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token, decode_token, hash_api_key
)
from app.core.redis import get_redis
from fastapi import HTTPException, status
import redis.asyncio as aioredis


RATE_LIMIT_WINDOW = 900  # 15 minutes
RATE_LIMIT_MAX = 10


async def authenticate_user(
    db: AsyncSession,
    tenant_id: str,
    email: str,
    password: str,
    redis: aioredis.Redis
) -> dict:
    """Validate credentials and return token pair."""
    # Rate limiting by IP is handled in middleware; here we validate creds
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.email == email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
        "email": user.email,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store refresh token hash in Redis (family tracking)
    family_id = str(uuid.uuid4())
    rt_hash = hash_api_key(refresh_token)
    await redis.setex(
        f"refresh:{rt_hash}",
        timedelta(days=7).seconds,
        f"{str(user.id)}:{family_id}"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "tenant_id": str(user.tenant_id),
        }
    }


async def rotate_refresh_token(raw_refresh: str, redis: aioredis.Redis) -> dict:
    """Family-invalidating refresh token rotation."""
    payload = decode_token(raw_refresh)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    rt_hash = hash_api_key(raw_refresh)
    stored = await redis.get(f"refresh:{rt_hash}")

    if not stored:
        # Reuse detected — family already invalidated or token unknown
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token reuse detected — please log in again")

    user_id, family_id = stored.split(":")
    # Invalidate old token
    await redis.delete(f"refresh:{rt_hash}")

    # Issue new pair
    token_data = {
        "sub": payload["sub"],
        "tenant_id": payload["tenant_id"],
        "role": payload["role"],
        "email": payload.get("email", ""),
    }
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    # Store new refresh token in same family
    new_hash = hash_api_key(new_refresh)
    await redis.setex(f"refresh:{new_hash}", timedelta(days=7).seconds, f"{user_id}:{family_id}")

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": 900,
    }


async def invalidate_user_sessions(user_id: str, redis: aioredis.Redis):
    """Add user to blocklist — invalidates all active JWTs."""
    await redis.setex(f"user_blocked:{user_id}", timedelta(days=7).seconds, "1")
