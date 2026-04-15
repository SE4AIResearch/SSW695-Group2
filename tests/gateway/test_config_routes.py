from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from buma.core.config import Settings, get_settings
from buma.gateway.app import create_app
from buma.gateway.deps import get_config_service, require_session
from buma.gateway.services.config import (
    ConfigService,
    DeveloperAlreadyExistsError,
    DeveloperNotFoundError,
    RepoNotFoundError,
)
from buma.schemas.api.developer_profile import DeveloperProfileResponse
from buma.schemas.api.repo_config import RepoConfigListResponse, RepoConfigResponse, RepoConfigSettings

NOW = datetime(2024, 1, 1, tzinfo=UTC)

REPO_RESPONSE = RepoConfigResponse(
    repo_id=42,
    installation_id=999,
    repo_full_name="org/repo",
    config=RepoConfigSettings(),
    created_at=NOW,
    updated_at=NOW,
)

DEV_RESPONSE = DeveloperProfileResponse(
    id=1,
    repo_id=42,
    github_login="alice",
    skills=["bug"],
    max_capacity=5,
    open_assignments=0,
    created_at=NOW,
    updated_at=NOW,
)


LIST_RESPONSE = RepoConfigListResponse(repos=[REPO_RESPONSE], total=1, limit=100, offset=0)


@pytest.fixture
def mock_svc():
    svc = AsyncMock(spec=ConfigService)
    svc.list_repos = AsyncMock(return_value=LIST_RESPONSE)
    svc.enroll_repo = AsyncMock(return_value=REPO_RESPONSE)
    svc.get_repo = AsyncMock(return_value=REPO_RESPONSE)
    svc.update_repo_config = AsyncMock(return_value=REPO_RESPONSE)
    svc.add_developer = AsyncMock(return_value=DEV_RESPONSE)
    svc.update_developer = AsyncMock(return_value=DEV_RESPONSE)
    svc.remove_developer = AsyncMock(return_value=None)
    return svc


@pytest.fixture
def test_settings():
    return Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="secret",
    )


@pytest.fixture
async def client(test_settings, mock_svc):
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_config_service] = lambda: mock_svc
    app.dependency_overrides[require_session] = lambda: "test-user"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ------------------------------------------------------------------
# Auth enforcement
# ------------------------------------------------------------------


@pytest.fixture
async def unauthed_client(test_settings, mock_svc):
    """Client with no session — require_session is NOT overridden."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_config_service] = lambda: mock_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_unauthenticated_request_returns_401(unauthed_client):
    response = await unauthed_client.get("/api/config/repos/42")
    assert response.status_code == 401


# ------------------------------------------------------------------
# GET /api/config/repos
# ------------------------------------------------------------------


async def test_list_repos_returns_200(client):
    response = await client.get("/api/config/repos")
    assert response.status_code == 200


async def test_list_repos_response_shape(client):
    response = await client.get("/api/config/repos")
    data = response.json()
    assert "repos" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


async def test_list_repos_default_pagination(client):
    response = await client.get("/api/config/repos")
    data = response.json()
    assert data["limit"] == 100
    assert data["offset"] == 0


async def test_list_repos_custom_pagination(client, mock_svc):
    mock_svc.list_repos.return_value = RepoConfigListResponse(repos=[], total=0, limit=10, offset=20)
    response = await client.get("/api/config/repos?limit=10&offset=20")
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 20


async def test_list_repos_contains_repo(client):
    response = await client.get("/api/config/repos")
    data = response.json()
    assert len(data["repos"]) == 1
    assert data["repos"][0]["repo_full_name"] == "org/repo"


async def test_list_repos_invalid_limit_returns_422(client):
    response = await client.get("/api/config/repos?limit=0")
    assert response.status_code == 422


async def test_list_repos_limit_exceeds_max_returns_422(client):
    response = await client.get("/api/config/repos?limit=501")
    assert response.status_code == 422


# ------------------------------------------------------------------
# POST /api/config/repos
# ------------------------------------------------------------------


async def test_enroll_repo_returns_201(client):
    response = await client.post(
        "/api/config/repos",
        json={"installation_id": 999, "repo_full_name": "org/repo"},
    )
    assert response.status_code == 201
    assert response.json()["repo_id"] == 42


async def test_enroll_repo_missing_field_returns_422(client):
    response = await client.post("/api/config/repos", json={"installation_id": 999})
    assert response.status_code == 422


# ------------------------------------------------------------------
# GET /api/config/repos/{repo_id}
# ------------------------------------------------------------------


async def test_get_repo_returns_200(client):
    response = await client.get("/api/config/repos/42")
    assert response.status_code == 200
    assert response.json()["repo_full_name"] == "org/repo"


async def test_get_repo_not_found_returns_404(client, mock_svc):
    mock_svc.get_repo.side_effect = RepoNotFoundError(99)
    response = await client.get("/api/config/repos/99")
    assert response.status_code == 404


# ------------------------------------------------------------------
# PATCH /api/config/repos/{repo_id}
# ------------------------------------------------------------------


VALID_CONFIG_BODY = {
    "config": {
        "label_map": {"categories": {}, "priorities": {}},
        "defaults": {"category": "bug", "priority": "P2"},
    }
}


async def test_update_repo_config_returns_200(client):
    response = await client.patch("/api/config/repos/42", json=VALID_CONFIG_BODY)
    assert response.status_code == 200


async def test_update_repo_config_not_found_returns_404(client, mock_svc):
    mock_svc.update_repo_config.side_effect = RepoNotFoundError(99)
    response = await client.patch("/api/config/repos/99", json=VALID_CONFIG_BODY)
    assert response.status_code == 404


async def test_update_repo_invalid_config_returns_422(client):
    response = await client.patch(
        "/api/config/repos/42",
        json={"config": {"defaults": {"category": "not-a-category", "priority": "P2"}}},
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# POST /api/config/repos/{repo_id}/developers
# ------------------------------------------------------------------


async def test_add_developer_returns_201(client):
    response = await client.post(
        "/api/config/repos/42/developers",
        json={"github_login": "alice", "skills": ["bug"], "max_capacity": 5},
    )
    assert response.status_code == 201
    assert response.json()["github_login"] == "alice"


async def test_add_developer_repo_not_found_returns_404(client, mock_svc):
    mock_svc.add_developer.side_effect = RepoNotFoundError(99)
    response = await client.post(
        "/api/config/repos/99/developers",
        json={"github_login": "alice"},
    )
    assert response.status_code == 404


async def test_add_developer_duplicate_returns_409(client, mock_svc):
    mock_svc.add_developer.side_effect = DeveloperAlreadyExistsError("alice")
    response = await client.post(
        "/api/config/repos/42/developers",
        json={"github_login": "alice"},
    )
    assert response.status_code == 409


async def test_add_developer_invalid_skill_returns_422(client):
    response = await client.post(
        "/api/config/repos/42/developers",
        json={"github_login": "alice", "skills": ["devops"]},
    )
    assert response.status_code == 422


# ------------------------------------------------------------------
# PATCH /api/config/repos/{repo_id}/developers/{login}
# ------------------------------------------------------------------


async def test_update_developer_returns_200(client):
    response = await client.patch(
        "/api/config/repos/42/developers/alice",
        json={"skills": ["bug", "feature"]},
    )
    assert response.status_code == 200


async def test_update_developer_not_found_returns_404(client, mock_svc):
    mock_svc.update_developer.side_effect = DeveloperNotFoundError("ghost")
    response = await client.patch(
        "/api/config/repos/42/developers/ghost",
        json={"skills": ["bug"]},
    )
    assert response.status_code == 404


# ------------------------------------------------------------------
# DELETE /api/config/repos/{repo_id}/developers/{login}
# ------------------------------------------------------------------


async def test_remove_developer_returns_204(client):
    response = await client.delete("/api/config/repos/42/developers/alice")
    assert response.status_code == 204


async def test_remove_developer_not_found_returns_404(client, mock_svc):
    mock_svc.remove_developer.side_effect = DeveloperNotFoundError("ghost")
    response = await client.delete("/api/config/repos/42/developers/ghost")
    assert response.status_code == 404
