"""
Auth routes — JWT issuance, refresh rotation, SSO redirect.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.redis import get_redis
from app.core.deps import get_current_user
from app.services.auth_service import authenticate_user, rotate_refresh_token
import redis.asyncio as aioredis

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


@router.post("/token", response_model=TokenResponse, summary="Issue JWT")
async def login(
    payload: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    """Authenticate and return access token. Refresh token set in httpOnly cookie."""
    import uuid
    result = await authenticate_user(db, uuid.UUID(payload.tenant_id), payload.email, payload.password, redis)

    # Set refresh token as httpOnly Secure SameSite=Strict cookie
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 3600,
        path="/api/v1/auth/refresh",
    )
    return TokenResponse(
        access_token=result["access_token"],
        token_type="bearer",
        expires_in=900,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotate refresh token")
async def refresh(
    response: Response,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    """Rotate refresh token using httpOnly cookie. Family invalidation on reuse."""
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    result = await rotate_refresh_token(refresh_token, redis)

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True, secure=True, samesite="strict",
        max_age=7 * 24 * 3600, path="/api/v1/auth/refresh",
    )
    return TokenResponse(access_token=result["access_token"], token_type="bearer", expires_in=900)


@router.post("/logout", summary="Invalidate session")
async def logout(
    response: Response,
    current_user: Annotated[dict, Depends(get_current_user)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
):
    """Blocklist current JTI and clear refresh cookie."""
    jti = current_user.get("jti")
    if jti:
        from datetime import timedelta
        await redis.setex(f"blocklist:{jti}", timedelta(days=1).seconds, "1")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", summary="Current user profile")
async def me(current_user: Annotated[dict, Depends(get_current_user)]):
    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "tenant_id": current_user.get("tenant_id"),
    }
