from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from buma.core.config import Settings, get_settings
from buma.gateway.app import create_app
from buma.gateway.services.oauth import COOKIE_NAME, OAuthService


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
# GET /auth/github
# ------------------------------------------------------------------


async def test_github_login_redirects_to_github(client):
    response = await client.get("/auth/github", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert "github.com/login/oauth/authorize" in location


async def test_github_login_includes_client_id(client):
    response = await client.get("/auth/github", follow_redirects=False)
    assert "client_id=test-client-id" in response.headers["location"]


async def test_github_login_includes_scope(client):
    response = await client.get("/auth/github", follow_redirects=False)
    assert "scope=read%3Auser" in response.headers["location"] or "scope=read:user" in response.headers["location"]


async def test_github_login_includes_state(client):
    response = await client.get("/auth/github", follow_redirects=False)
    assert "state=" in response.headers["location"]


async def test_github_login_state_differs_per_request(client):
    """Each redirect must generate a fresh state value."""
    r1 = await client.get("/auth/github", follow_redirects=False)
    r2 = await client.get("/auth/github", follow_redirects=False)
    state1 = [p for p in r1.headers["location"].split("&") if p.startswith("state=")][0]
    state2 = [p for p in r2.headers["location"].split("&") if p.startswith("state=")][0]
    assert state1 != state2


# ------------------------------------------------------------------
# GET /auth/callback
# ------------------------------------------------------------------


async def test_callback_success_returns_200(client):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        response = await client.get("/auth/callback?code=test-code")
    assert response.status_code == 200


async def test_callback_success_returns_login(client):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        response = await client.get("/auth/callback?code=test-code")
    assert response.json()["login"] == "octocat"


async def test_callback_success_sets_session_cookie(client):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        response = await client.get("/auth/callback?code=test-code")
    assert COOKIE_NAME in response.cookies


async def test_callback_cookie_is_valid_jwt(client, oauth_settings):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        response = await client.get("/auth/callback?code=test-code")
    cookie_value = response.cookies[COOKIE_NAME]
    svc = OAuthService(oauth_settings)
    login = svc.get_session_user(cookie_value)
    assert login == "octocat"


async def test_callback_exchange_failure_returns_502(client):
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(side_effect=Exception("GitHub down"))):
        response = await client.get("/auth/callback?code=bad-code")
    assert response.status_code == 502


async def test_callback_missing_code_returns_422(client):
    response = await client.get("/auth/callback")
    assert response.status_code == 422


# ------------------------------------------------------------------
# POST /auth/logout
# ------------------------------------------------------------------


async def test_logout_returns_200(client):
    response = await client.post("/auth/logout")
    assert response.status_code == 200


async def test_logout_returns_status_message(client):
    response = await client.post("/auth/logout")
    assert response.json() == {"status": "logged out"}


async def test_logout_clears_cookie(client):
    # Set a cookie first via callback, then log out
    with patch.object(OAuthService, "exchange_code", new=AsyncMock(return_value="octocat")):
        login_resp = await client.get("/auth/callback?code=test-code")
    assert COOKIE_NAME in login_resp.cookies

    logout_resp = await client.post("/auth/logout")
    # After logout the cookie should be deleted (empty value or absent)
    cookie_after = logout_resp.cookies.get(COOKIE_NAME, "")
    assert cookie_after == ""


# ------------------------------------------------------------------
# OAuthService unit tests (JWT)
# ------------------------------------------------------------------


def test_create_session_returns_string(oauth_settings):
    svc = OAuthService(oauth_settings)
    token = svc.create_session("octocat")
    assert isinstance(token, str)
    assert len(token) > 0


def test_get_session_user_valid_token(oauth_settings):
    svc = OAuthService(oauth_settings)
    token = svc.create_session("octocat")
    assert svc.get_session_user(token) == "octocat"


def test_get_session_user_tampered_token(oauth_settings):
    svc = OAuthService(oauth_settings)
    token = svc.create_session("octocat")
    tampered = token[:-4] + "xxxx"
    assert svc.get_session_user(tampered) is None


def test_get_session_user_wrong_secret(oauth_settings):
    svc = OAuthService(oauth_settings)
    token = svc.create_session("octocat")

    other_settings = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="secret",
        session_secret="completely-different-secret-32b!",
    )
    other_svc = OAuthService(other_settings)
    assert other_svc.get_session_user(token) is None


def test_get_session_user_garbage_input(oauth_settings):
    svc = OAuthService(oauth_settings)
    assert svc.get_session_user("not.a.jwt") is None
    assert svc.get_session_user("") is None


def test_get_session_user_expired_token(oauth_settings):
    """A token whose exp is in the past should be rejected."""
    import time

    import jwt as pyjwt

    payload = {"sub": "octocat", "exp": int(time.time()) - 1}
    expired_token = pyjwt.encode(payload, oauth_settings.session_secret, algorithm="HS256")
    svc = OAuthService(oauth_settings)
    assert svc.get_session_user(expired_token) is None


def test_build_redirect_url_contains_client_id(oauth_settings):
    svc = OAuthService(oauth_settings)
    url = svc.build_redirect_url("mystate")
    assert "client_id=test-client-id" in url
    assert "state=mystate" in url
    assert "scope=read:user" in url
