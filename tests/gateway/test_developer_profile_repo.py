from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from buma.gateway.repositories.developer_profile import DeveloperProfileRepository

REPO_ID = 42


def _scalar_result(record):
    result = MagicMock()
    result.scalar_one_or_none.return_value = record
    return result


def _scalars_result(records):
    result = MagicMock()
    result.scalars.return_value.all.return_value = records
    return result


def _make_dev(login="alice", skills=None, max_capacity=5, open_assignments=0):
    record = MagicMock()
    record.repo_id = REPO_ID
    record.github_login = login
    record.skills = skills or ["bug"]
    record.max_capacity = max_capacity
    record.open_assignments = open_assignments
    record.updated_at = datetime(2024, 1, 1, tzinfo=UTC)
    return record


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def repo(mock_session):
    return DeveloperProfileRepository(session=mock_session)


async def test_create_adds_and_flushes(repo, mock_session):
    await repo.create(repo_id=REPO_ID, github_login="alice", skills=["bug"], max_capacity=5)
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


async def test_get_by_login_found(repo, mock_session):
    record = _make_dev()
    mock_session.execute = AsyncMock(return_value=_scalar_result(record))
    result = await repo.get_by_login(REPO_ID, "alice")
    assert result is record


async def test_get_by_login_not_found(repo, mock_session):
    mock_session.execute = AsyncMock(return_value=_scalar_result(None))
    result = await repo.get_by_login(REPO_ID, "nobody")
    assert result is None


async def test_list_for_repo_returns_all(repo, mock_session):
    records = [_make_dev("alice"), _make_dev("bob")]
    mock_session.execute = AsyncMock(return_value=_scalars_result(records))
    result = await repo.list_for_repo(REPO_ID)
    assert len(result) == 2


async def test_list_for_repo_empty(repo, mock_session):
    mock_session.execute = AsyncMock(return_value=_scalars_result([]))
    result = await repo.list_for_repo(REPO_ID)
    assert result == []


async def test_update_skills_and_capacity(repo, mock_session):
    record = _make_dev()
    mock_session.execute = AsyncMock(return_value=_scalar_result(record))
    result = await repo.update(REPO_ID, "alice", skills=["bug", "feature"], max_capacity=8)
    assert result is record
    assert record.skills == ["bug", "feature"]
    assert record.max_capacity == 8
    mock_session.flush.assert_called_once()


async def test_update_partial_skills_only(repo, mock_session):
    record = _make_dev(max_capacity=5)
    mock_session.execute = AsyncMock(return_value=_scalar_result(record))
    await repo.update(REPO_ID, "alice", skills=["security"], max_capacity=None)
    assert record.skills == ["security"]
    assert record.max_capacity == 5  # unchanged


async def test_update_returns_none_when_not_found(repo, mock_session):
    mock_session.execute = AsyncMock(return_value=_scalar_result(None))
    result = await repo.update(REPO_ID, "ghost", skills=["bug"], max_capacity=None)
    assert result is None
    mock_session.flush.assert_not_called()


async def test_delete_returns_true_when_found(repo, mock_session):
    record = _make_dev()
    mock_session.execute = AsyncMock(return_value=_scalar_result(record))
    result = await repo.delete(REPO_ID, "alice")
    assert result is True
    mock_session.delete.assert_called_once_with(record)
    mock_session.flush.assert_called_once()


async def test_delete_returns_false_when_not_found(repo, mock_session):
    mock_session.execute = AsyncMock(return_value=_scalar_result(None))
    result = await repo.delete(REPO_ID, "ghost")
    assert result is False
    mock_session.delete.assert_not_called()
