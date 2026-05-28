"""
Unit tests — Authentication module
TC-AUTH-001 to TC-AUTH-010
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_login_missing_fields():
    """TC-AUTH-002: Login with missing fields returns 422"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/auth/token", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_email():
    """TC-AUTH-002: Invalid email format returns 422"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/auth/token", json={
            "email": "not-an-email", "password": "secret", "tenant_id": "00000000-0000-0000-0000-000000000001"
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint():
    """Infrastructure: /health returns 200"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_protected_route_requires_auth():
    """TC-APISEC-003: Protected routes return 401 without token"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/products/", headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_docs_available():
    """Swagger UI accessible at /api/docs"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/docs")
    assert response.status_code == 200


def test_jwt_token_creation():
    """TC-AUTH-001: JWT contains required claims"""
    from app.core.security import create_access_token, decode_token
    token = create_access_token({
        "sub": "user-123", "tenant_id": "tenant-456",
        "role": "store_manager", "email": "test@test.com"
    })
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["tenant_id"] == "tenant-456"
    assert payload["role"] == "store_manager"
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload


def test_refresh_token_different_from_access():
    """Refresh token has type=refresh, access has type=access"""
    from app.core.security import create_access_token, create_refresh_token, decode_token
    data = {"sub": "u1", "tenant_id": "t1", "role": "warehouse_op", "email": "x@x.com"}
    at = decode_token(create_access_token(data))
    rt = decode_token(create_refresh_token(data))
    assert at["type"] == "access"
    assert rt["type"] == "refresh"
    assert at["jti"] != rt["jti"]  # Different JTIs


def test_password_hash_and_verify():
    """Password hashing and verification work correctly"""
    from app.core.security import hash_password, verify_password
    plain = "SuperSecret123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_api_key_hash_deterministic():
    """SHA-256 hash of API key is deterministic"""
    from app.core.security import hash_api_key
    key = "test-api-key-abc123"
    assert hash_api_key(key) == hash_api_key(key)
    assert len(hash_api_key(key)) == 64  # SHA-256 hex = 64 chars
    assert hash_api_key(key) != hash_api_key("different-key")
