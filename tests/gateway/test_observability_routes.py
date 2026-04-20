from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from buma.core.config import Settings, get_settings
from buma.gateway.app import create_app
from buma.gateway.deps import get_db, require_session


def _make_issue_orm(event_id="evt-1", issue_number=1, title="Test bug", repo_id=42):
    i = MagicMock()
    i.event_id = event_id
    i.repo_id = repo_id
    i.issue_number = issue_number
    i.title = title
    i.body = "A bug description"
    i.labels = ["bug"]
    i.author_login = "alice"
    i.issue_created_at = datetime(2024, 1, 1, tzinfo=UTC)
    i.issue_updated_at = datetime(2024, 1, 1, tzinfo=UTC)
    i.snapshot_at = datetime(2024, 1, 1, tzinfo=UTC)
    return i


def _make_issues_db(repo_exists=True, issue_rows=None, total=None):
    session = AsyncMock()

    repo_scalar = MagicMock()
    repo_scalar.scalar_one_or_none.return_value = MagicMock() if repo_exists else None

    count_scalar = MagicMock()
    count_scalar.scalar_one.return_value = total if total is not None else len(issue_rows or [])

    rows_scalar = MagicMock()
    rows_scalar.scalars.return_value.all.return_value = issue_rows or []

    session.execute = AsyncMock(side_effect=[repo_scalar, count_scalar, rows_scalar])
    return session


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
    app.dependency_overrides[require_session] = lambda: "test-user"
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ------------------------------------------------------------------
# Auth enforcement
# ------------------------------------------------------------------


async def test_triage_unauthenticated_returns_401(test_settings):
    """require_session NOT overridden — no cookie → 401."""
    db = _make_db_session(repo_exists=True, triage_rows=[], total=0)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/triage/42")
    assert response.status_code == 401


async def test_workload_unauthenticated_returns_401(test_settings):
    db = _make_workload_db(repo_exists=True, dev_rows=[])
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/workload/42")
    assert response.status_code == 401


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


# ------------------------------------------------------------------
# GET /api/productivity/{repo_id}
# ------------------------------------------------------------------


def _make_productivity_db(repo_exists=True, agg_rows=None, bucket_rows=None):
    """Mock session for the productivity endpoint (3 execute calls)."""
    session = AsyncMock()

    repo_result = MagicMock()
    repo_result.scalar_one_or_none.return_value = MagicMock() if repo_exists else None

    agg_result = MagicMock()
    agg_result.mappings.return_value.all.return_value = agg_rows or []

    bucket_result = MagicMock()
    bucket_result.mappings.return_value.all.return_value = bucket_rows or []

    session.execute = AsyncMock(side_effect=[repo_result, agg_result, bucket_result])
    return session


_SAMPLE_AGG = [
    {
        "github_login": "alice",
        "open_assignments": 2,
        "max_capacity": 5,
        "resolved_count": 3,
        "avg_resolution_hours": 24.0,
    }
]

_SAMPLE_BUCKETS = [
    {"github_login": "alice", "period_start": "2026-04-13", "resolved": 1},
    {"github_login": "alice", "period_start": "2026-04-14", "resolved": 2},
]


async def test_productivity_unauthenticated_returns_401(test_settings):
    db = _make_productivity_db()
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/productivity/42")
    assert response.status_code == 401


async def test_productivity_repo_not_found_returns_404(test_settings):
    db = _make_productivity_db(repo_exists=False)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/productivity/99")
    assert response.status_code == 404


async def test_productivity_returns_200(test_settings):
    db = _make_productivity_db(agg_rows=_SAMPLE_AGG, bucket_rows=_SAMPLE_BUCKETS)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/productivity/42")
    assert response.status_code == 200


async def test_productivity_response_shape(test_settings):
    db = _make_productivity_db(agg_rows=_SAMPLE_AGG, bucket_rows=_SAMPLE_BUCKETS)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/productivity/42")
    data = response.json()
    assert data["repo_id"] == 42
    assert "window" in data
    assert "developers" in data


async def test_productivity_developer_fields(test_settings):
    db = _make_productivity_db(agg_rows=_SAMPLE_AGG, bucket_rows=_SAMPLE_BUCKETS)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/productivity/42")
    dev = response.json()["developers"][0]
    assert dev["github_login"] == "alice"
    assert dev["resolved_count"] == 3
    assert dev["avg_resolution_hours"] == 24.0
    assert dev["open_assignments"] == 2
    assert dev["max_capacity"] == 5
    assert "buckets" in dev


async def test_productivity_default_window_is_30d(test_settings):
    db = _make_productivity_db(agg_rows=[], bucket_rows=[])
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/productivity/42")
    assert response.json()["window"] == "30d"


async def test_productivity_accepts_all_windows(test_settings):
    for window in ("7d", "30d", "90d", "all"):
        db = _make_productivity_db(agg_rows=[], bucket_rows=[])
        async with await _make_client(test_settings, db) as client:
            response = await client.get(f"/api/productivity/42?window={window}")
        assert response.status_code == 200, f"window={window} failed"
        assert response.json()["window"] == window


async def test_productivity_invalid_window_returns_422(test_settings):
    db = _make_productivity_db(agg_rows=[], bucket_rows=[])
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/productivity/42?window=1y")
    assert response.status_code == 422


async def test_productivity_empty_team_returns_200(test_settings):
    db = _make_productivity_db(agg_rows=[], bucket_rows=[])
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/productivity/42")
    data = response.json()
    assert response.status_code == 200
    assert data["developers"] == []


# ------------------------------------------------------------------
# GET /api/issues/{repo_id}
# ------------------------------------------------------------------


async def test_issues_unauthenticated_returns_401(test_settings):
    db = _make_issues_db(repo_exists=True, issue_rows=[], total=0)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/issues/42")
    assert response.status_code == 401


async def test_issues_repo_not_found_returns_404(test_settings):
    db = _make_issues_db(repo_exists=False)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/99")
    assert response.status_code == 404


async def test_issues_returns_200(test_settings):
    rows = [_make_issue_orm("evt-1", 1), _make_issue_orm("evt-2", 2)]
    db = _make_issues_db(repo_exists=True, issue_rows=rows, total=2)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/42")
    assert response.status_code == 200


async def test_issues_response_shape(test_settings):
    rows = [_make_issue_orm("evt-1", 1)]
    db = _make_issues_db(repo_exists=True, issue_rows=rows, total=1)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/42")
    data = response.json()
    assert data["repo_id"] == 42
    assert data["total"] == 1
    assert len(data["issues"]) == 1


async def test_issues_issue_fields(test_settings):
    rows = [_make_issue_orm("evt-1", 7, "Crash on login")]
    db = _make_issues_db(repo_exists=True, issue_rows=rows, total=1)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/42")
    issue = response.json()["issues"][0]
    assert issue["event_id"] == "evt-1"
    assert issue["issue_number"] == 7
    assert issue["title"] == "Crash on login"
    assert issue["author_login"] == "alice"
    assert issue["labels"] == ["bug"]


async def test_issues_default_pagination(test_settings):
    db = _make_issues_db(repo_exists=True, issue_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/42")
    data = response.json()
    assert data["limit"] == 100
    assert data["offset"] == 0


async def test_issues_custom_pagination(test_settings):
    db = _make_issues_db(repo_exists=True, issue_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/42?limit=25&offset=50")
    data = response.json()
    assert data["limit"] == 25
    assert data["offset"] == 50


async def test_issues_invalid_limit_returns_422(test_settings):
    db = _make_issues_db(repo_exists=True, issue_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/42?limit=0")
    assert response.status_code == 422


async def test_issues_limit_exceeds_max_returns_422(test_settings):
    db = _make_issues_db(repo_exists=True, issue_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/42?limit=501")
    assert response.status_code == 422


async def test_issues_empty_repo_returns_200(test_settings):
    db = _make_issues_db(repo_exists=True, issue_rows=[], total=0)
    async with await _make_client(test_settings, db) as client:
        response = await client.get("/api/issues/42")
    data = response.json()
    assert response.status_code == 200
    assert data["issues"] == []
    assert data["total"] == 0
