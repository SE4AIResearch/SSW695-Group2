from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from buma.core.config import Settings, get_settings
from buma.gateway.app import create_app
from buma.gateway.deps import get_db


def _make_triage_orm(event_id="evt-1", issue_number=1, category="bug", priority="P1"):
    r = MagicMock()
    r.event_id = event_id
    r.delivery_id = "del-1"
    r.repo_id = 42
    r.issue_number = issue_number
    r.decided_at = datetime(2024, 1, 1, tzinfo=UTC)
    r.predicted_category = category
    r.predicted_priority = priority
    r.confidence = 0.9
    r.selected_assignee_login = "alice"
    r.explanation = "assigned"
    r.patch_state = "APPLIED"
    r.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    r.updated_at = datetime(2024, 1, 1, tzinfo=UTC)
    return r


def _make_dev_orm(login="alice", max_capacity=5, open_assignments=2):
    d = MagicMock()
    d.github_login = login
    d.skills = ["bug"]
    d.max_capacity = max_capacity
    d.open_assignments = open_assignments
    return d


def _make_db_session(repo_exists=True, triage_rows=None, dev_rows=None, total=None):
    """Build a mock AsyncSession that covers all execute() patterns used by observability routes."""
    session = AsyncMock()

    repo_scalar = MagicMock()
    repo_scalar.scalar_one_or_none.return_value = MagicMock() if repo_exists else None

    count_scalar = MagicMock()
    count_scalar.scalar_one.return_value = total if total is not None else len(triage_rows or [])

    rows_scalar = MagicMock()
    rows_scalar.scalars.return_value.all.return_value = triage_rows or dev_rows or []

    # Each call to session.execute() returns the next mock in sequence
    session.execute = AsyncMock(side_effect=[repo_scalar, count_scalar, rows_scalar])
    return session


def _make_workload_db(repo_exists=True, dev_rows=None):
    session = AsyncMock()

    repo_scalar = MagicMock()
    repo_scalar.scalar_one_or_none.return_value = MagicMock() if repo_exists else None

    rows_scalar = MagicMock()
    rows_scalar.scalars.return_value.all.return_value = dev_rows or []

    session.execute = AsyncMock(side_effect=[repo_scalar, rows_scalar])
    return session


@pytest.fixture
def test_settings():
    return Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="secret",
    )


async def _make_client(test_settings, db_session):
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = lambda: db_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ------------------------------------------------------------------
# GET /api/triage/{repo_id}
# ------------------------------------------------------------------


async def test_triage_history_returns_200(test_settings):
    rows = [_make_triage_orm("evt-1"), _make_triage_orm("evt-2")]
    db = _make_db_session(repo_exists=True, triage_rows=rows, total=2)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/triage/42")
    assert response.status_code == 200
    data = response.json()
    assert data["repo_id"] == 42
    assert data["total"] == 2
    assert len(data["decisions"]) == 2


async def test_triage_history_default_pagination(test_settings):
    db = _make_db_session(repo_exists=True, triage_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/triage/42")
    data = response.json()
    assert data["limit"] == 100
    assert data["offset"] == 0


async def test_triage_history_custom_pagination(test_settings):
    db = _make_db_session(repo_exists=True, triage_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/triage/42?limit=10&offset=20")
    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 20


async def test_triage_history_repo_not_found_returns_404(test_settings):
    db = _make_db_session(repo_exists=False)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/triage/99")
    assert response.status_code == 404


async def test_triage_history_invalid_limit_returns_422(test_settings):
    db = _make_db_session(repo_exists=True, triage_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/triage/42?limit=0")
    assert response.status_code == 422


async def test_triage_history_limit_exceeds_max_returns_422(test_settings):
    db = _make_db_session(repo_exists=True, triage_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/triage/42?limit=501")
    assert response.status_code == 422


# ------------------------------------------------------------------
# GET /api/workload/{repo_id}
# ------------------------------------------------------------------


async def test_workload_returns_200(test_settings):
    devs = [_make_dev_orm("alice", 5, 3), _make_dev_orm("bob", 5, 1)]
    db = _make_workload_db(repo_exists=True, dev_rows=devs)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/workload/42")
    assert response.status_code == 200
    data = response.json()
    assert data["repo_id"] == 42
    assert len(data["developers"]) == 2
    assert data["developers"][0]["github_login"] == "alice"
    assert data["developers"][0]["available_capacity"] == 2


async def test_workload_repo_not_found_returns_404(test_settings):
    db = _make_workload_db(repo_exists=False)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/workload/99")
    assert response.status_code == 404


async def test_workload_empty_team(test_settings):
    db = _make_workload_db(repo_exists=True, dev_rows=[])
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/workload/42")
    assert response.status_code == 200
    assert response.json()["developers"] == []
