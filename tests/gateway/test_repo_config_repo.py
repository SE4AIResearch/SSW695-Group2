from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from buma.gateway.repositories.repo_config import RepoConfigRepository

REPO_ID = 42
CONFIG = {"label_map": {"categories": {}, "priorities": {}}, "defaults": {"category": "bug", "priority": "P2"}}


def _scalar_result(record):
    """Return a mock mimicking session.execute(...).scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = record
    return result


def _make_repo_record():
    record = MagicMock()
    record.repo_id = REPO_ID
    record.installation_id = 999
    record.repo_full_name = "org/repo"
    record.config = CONFIG
    record.updated_at = datetime(2024, 1, 1, tzinfo=UTC)
    return record


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def repo(mock_session):
    return RepoConfigRepository(session=mock_session)


async def test_create_adds_and_flushes(repo, mock_session):
    await repo.create(installation_id=999, repo_full_name="org/repo", config=CONFIG)
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


async def test_create_returns_repo_config_orm(repo):
    result = await repo.create(installation_id=999, repo_full_name="org/repo", config=CONFIG)
    assert result is not None


async def test_get_by_id_found(repo, mock_session):
    record = _make_repo_record()
    mock_session.execute = AsyncMock(return_value=_scalar_result(record))
    result = await repo.get_by_id(REPO_ID)
    assert result is record


async def test_get_by_id_not_found(repo, mock_session):
    mock_session.execute = AsyncMock(return_value=_scalar_result(None))
    result = await repo.get_by_id(REPO_ID)
    assert result is None


async def test_update_config_returns_updated_record(repo, mock_session):
    record = _make_repo_record()
    mock_session.execute = AsyncMock(return_value=_scalar_result(record))
    new_config = {**CONFIG, "defaults": {"category": "feature", "priority": "P1"}}
    result = await repo.update_config(REPO_ID, new_config)
    assert result is record
    assert record.config == new_config
    mock_session.flush.assert_called_once()


async def test_update_config_returns_none_when_not_found(repo, mock_session):
    mock_session.execute = AsyncMock(return_value=_scalar_result(None))
    result = await repo.update_config(REPO_ID, CONFIG)
    assert result is None
    mock_session.flush.assert_not_called()
