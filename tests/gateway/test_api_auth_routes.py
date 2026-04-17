from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from buma.core.config import Settings, get_settings
from buma.gateway.app import create_app
from buma.gateway.deps import get_config_service
from buma.gateway.services.config import RepoNotFoundError
from buma.gateway.services.oauth import OAuthService


@pytest.fixture
def oauth_settings():
    return Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="secret",
        github_oauth_client_id="test-client-id",
        github_oauth_client_secret="test-client-secret",
        session_secret="test-session-secret-32-bytes-long!",
    )


@pytest.fixture
async def client(oauth_settings):
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: oauth_settings
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ------------------------------------------------------------------
# POST /api/v1/auth/github
# ------------------------------------------------------------------


async def test_github_token_returns_200(client):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        response = await client.post("/api/v1/auth/github", json={"code": "test-code"})
    assert response.status_code == 200


async def test_github_token_returns_token(client):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        response = await client.post("/api/v1/auth/github", json={"code": "test-code"})
    assert "token" in response.json()
    assert isinstance(response.json()["token"], str)


async def test_github_token_returns_user(client):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        response = await client.post("/api/v1/auth/github", json={"code": "test-code"})
    user = response.json()["user"]
    assert user["login"] == "octocat"
    assert user["github_username"] == "octocat"
    assert user["name"] == "octocat"


async def test_github_token_is_valid_jwt(client, oauth_settings):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        response = await client.post("/api/v1/auth/github", json={"code": "test-code"})
    token = response.json()["token"]
    svc = OAuthService(oauth_settings)
    assert svc.get_session_user(token) == "octocat"


async def test_github_token_exchange_failure_returns_502(client):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(side_effect=Exception("GitHub down"))):
        response = await client.post("/api/v1/auth/github", json={"code": "bad-code"})
    assert response.status_code == 502


async def test_github_token_missing_code_returns_422(client):
    response = await client.post("/api/v1/auth/github", json={})
    assert response.status_code == 422


# ------------------------------------------------------------------
# POST /api/v1/auth/login
# ------------------------------------------------------------------


async def test_email_login_returns_501(client):
    response = await client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "pw"})
    assert response.status_code == 501


async def test_email_login_missing_fields_returns_422(client):
    response = await client.post("/api/v1/auth/login", json={"email": "a@b.com"})
    assert response.status_code == 422


# ------------------------------------------------------------------
# require_session — Bearer token enforcement
# ------------------------------------------------------------------


async def test_bearer_token_grants_access(oauth_settings):
    """A valid JWT in the Authorization header should pass require_session (auth layer only)."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: oauth_settings
    # Override config service so we don't need a real DB — 404 means auth passed
    mock_svc = AsyncMock()
    mock_svc.get_repo = AsyncMock(side_effect=RepoNotFoundError(1))
    app.dependency_overrides[get_config_service] = lambda: mock_svc

    svc = OAuthService(oauth_settings)
    token = svc.create_session("octocat")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/config/repos/1", headers={"Authorization": f"Bearer {token}"})
    # Any status except 401 means the auth layer accepted the token
    assert response.status_code != 401


async def test_missing_authorization_header_returns_401(client):
    response = await client.get("/api/config/repos/1")
    assert response.status_code == 401


async def test_malformed_authorization_header_returns_401(client):
    response = await client.get("/api/config/repos/1", headers={"Authorization": "Token abc123"})
    assert response.status_code == 401


async def test_invalid_jwt_returns_401(client):
    response = await client.get("/api/config/repos/1", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401
