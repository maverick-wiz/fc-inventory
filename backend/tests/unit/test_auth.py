"""
Unit tests — Authentication module
TC-AUTH-001 through TC-AUTH-009
SCRUM-64: Core Auth Module
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_login_missing_fields():
    """TC-AUTH-002: Login with missing fields returns 422"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/token", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_email_format():
    """TC-AUTH-002: Login with invalid email format returns 422"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/token", json={
            "email": "not-an-email",
            "password": "secret",
            "tenant_id": "walmart"
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint():
    """Infrastructure: health check returns 200"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_docs_available():
    """API docs endpoint is accessible"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/docs")
    assert response.status_code == 200
