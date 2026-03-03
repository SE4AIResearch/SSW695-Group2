from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from buma.core.config import Settings, get_settings
from buma.gateway.app import create_app
from buma.gateway.deps import get_ingest_service
from buma.gateway.services.ingest import IngestResult, IngestService

TEST_SECRET = "test-secret"

SAMPLE_PAYLOAD = {
    "action": "opened",
    "installation": {"id": 12345},
    "repository": {"id": 111, "full_name": "owner/repo", "private": False},
    "issue": {
        "number": 1,
        "id": 999,
        "node_id": "I_node",
        "url": "https://api.github.com/repos/owner/repo/issues/1",
        "html_url": "https://github.com/owner/repo/issues/1",
        "title": "Bug",
        "body": None,
        "labels": [],
        "user": {"login": "octocat"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    },
}


def _sign(payload: bytes, secret: str = TEST_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256).hexdigest()


def _body(payload: dict = SAMPLE_PAYLOAD) -> bytes:
    return json.dumps(payload).encode()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret=TEST_SECRET,
    )


@pytest.fixture
def mock_service() -> IngestService:
    svc = AsyncMock(spec=IngestService)
    svc.handle = AsyncMock(return_value=IngestResult.QUEUED)
    return svc


@pytest.fixture
async def client(test_settings: Settings, mock_service: IngestService):
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_ingest_service] = lambda: mock_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_missing_event_header_returns_400(client: AsyncClient):
    body = _body()
    response = await client.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Delivery": "abc", "X-Hub-Signature-256": _sign(body)},
    )
    assert response.status_code == 400


async def test_missing_delivery_header_returns_400(client: AsyncClient):
    body = _body()
    response = await client.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "issues", "X-Hub-Signature-256": _sign(body)},
    )
    assert response.status_code == 400


async def test_invalid_signature_returns_401(client: AsyncClient):
    body = _body()
    response = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "abc",
            "X-Hub-Signature-256": "sha256=badhash",
        },
    )
    assert response.status_code == 401


async def test_queued_response(client: AsyncClient, mock_service: IngestService):
    mock_service.handle.return_value = IngestResult.QUEUED
    body = _body()
    response = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-123",
            "X-Hub-Signature-256": _sign(body),
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    assert data["delivery_id"] == "delivery-123"


async def test_duplicate_response(client: AsyncClient, mock_service: IngestService):
    mock_service.handle.return_value = IngestResult.DUPLICATE
    body = _body()
    response = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-123",
            "X-Hub-Signature-256": _sign(body),
        },
    )
    assert response.status_code == 202
    assert response.json()["status"] == "duplicate"


async def test_ignored_response(client: AsyncClient, mock_service: IngestService):
    mock_service.handle.return_value = IngestResult.IGNORED
    body = _body()
    response = await client.post(
        "/webhook/github",
        content=body,
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": "delivery-456",
            "X-Hub-Signature-256": _sign(body),
        },
    )
    assert response.status_code == 202
    assert response.json()["status"] == "ignored"
    assert response.json()["event"] == "push"
