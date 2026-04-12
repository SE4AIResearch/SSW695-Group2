from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from httpx import ASGITransport, AsyncClient

from buma.core.config import Settings, get_settings
from buma.gateway.app import create_app  # noqa: F401 (used via fixture)

SAMPLE_PAYLOAD = {
    "action": "opened",
    "installation": {"id": 99001},
    "repository": {"id": 123456789, "full_name": "org/repo", "private": False},
    "issue": {
        "number": 1,
        "id": 1,
        "node_id": "I_1",
        "url": "https://api.github.com/repos/org/repo/issues/1",
        "html_url": "https://github.com/org/repo/issues/1",
        "title": "Bug",
        "body": "Crash on startup",
        "labels": [],
        "user": {"login": "reporter"},
        "created_at": "2026-04-08T00:00:00Z",
        "updated_at": "2026-04-08T00:00:00Z",
    },
    "sender": {"login": "reporter"},
}


@pytest.fixture
def debug_settings():
    return Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="test-secret",
        debug=True,
    )


@pytest.fixture
def prod_settings():
    return Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="test-secret",
        debug=False,
    )


@pytest.fixture
async def debug_client(debug_settings):
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: debug_settings
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def prod_client(prod_settings):
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: prod_settings
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ------------------------------------------------------------------
# Endpoint not available in production
# ------------------------------------------------------------------


async def test_dev_sign_webhook_not_available_in_prod(prod_client):
    response = await prod_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    assert response.status_code == 404


# ------------------------------------------------------------------
# Endpoint available in debug mode
# ------------------------------------------------------------------


async def test_dev_sign_webhook_returns_200_in_debug(debug_client):
    response = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    assert response.status_code == 200


async def test_dev_sign_webhook_response_shape(debug_client):
    response = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    data = response.json()
    assert "x_github_event" in data
    assert "x_github_delivery" in data
    assert "x_hub_signature_256" in data
    assert "compact_body" in data


async def test_dev_sign_webhook_default_event_is_issues(debug_client):
    response = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    assert response.json()["x_github_event"] == "issues"


async def test_dev_sign_webhook_custom_event(debug_client):
    response = await debug_client.post("/dev/sign-webhook?event=push", json=SAMPLE_PAYLOAD)
    assert response.json()["x_github_event"] == "push"


async def test_dev_sign_webhook_delivery_id_is_uuid(debug_client):
    import re

    response = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    delivery_id = response.json()["x_github_delivery"]
    assert re.match(r"^[0-9a-f-]{36}$", delivery_id), f"Not a UUID: {delivery_id}"


async def test_dev_sign_webhook_compact_body_is_valid_json(debug_client):
    response = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    compact = response.json()["compact_body"]
    parsed = json.loads(compact)
    assert parsed["action"] == "opened"


async def test_dev_sign_webhook_signature_is_valid(debug_client):
    """The returned signature must validate against the returned compact body."""
    response = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    data = response.json()

    compact_body = data["compact_body"]
    sig_header = data["x_hub_signature_256"]

    expected = "sha256=" + hmac.new(b"test-secret", compact_body.encode(), hashlib.sha256).hexdigest()
    assert sig_header == expected


async def test_dev_sign_webhook_two_calls_produce_different_delivery_ids(debug_client):
    r1 = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    r2 = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    assert r1.json()["x_github_delivery"] != r2.json()["x_github_delivery"]


async def test_dev_sign_webhook_signature_changes_with_payload(debug_client):
    r1 = await debug_client.post("/dev/sign-webhook", json=SAMPLE_PAYLOAD)
    modified = {**SAMPLE_PAYLOAD, "action": "closed"}
    r2 = await debug_client.post("/dev/sign-webhook", json=modified)
    assert r1.json()["x_hub_signature_256"] != r2.json()["x_hub_signature_256"]
