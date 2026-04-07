from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from buma.gateway.repositories.developer_profile import DeveloperProfileRepository
from buma.gateway.repositories.repo_config import RepoConfigRepository
from buma.gateway.services.config import (
    ConfigService,
    DeveloperAlreadyExistsError,
    DeveloperNotFoundError,
    RepoNotFoundError,
)
from buma.schemas.api.developer_profile import DeveloperProfileCreate, DeveloperProfileUpdate
from buma.schemas.api.repo_config import RepoConfigCreate, RepoConfigSettings, RepoConfigUpdate

NOW = datetime(2024, 1, 1, tzinfo=UTC)


def _make_repo_orm(repo_id=42):
    r = MagicMock()
    r.repo_id = repo_id
    r.installation_id = 999
    r.repo_full_name = "org/repo"
    r.config = {"label_map": {"categories": {}, "priorities": {}}, "defaults": {"category": "bug", "priority": "P2"}}
    r.created_at = NOW
    r.updated_at = NOW
    return r


def _make_dev_orm(login="alice"):
    d = MagicMock()
    d.id = 1
    d.repo_id = 42
    d.github_login = login
    d.skills = ["bug"]
    d.max_capacity = 5
    d.open_assignments = 0
    d.created_at = NOW
    d.updated_at = NOW
    return d


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_repo_config_repo():
    return AsyncMock(spec=RepoConfigRepository)


@pytest.fixture
def mock_dev_repo():
    return AsyncMock(spec=DeveloperProfileRepository)


@pytest.fixture
def svc(mock_session, mock_repo_config_repo, mock_dev_repo):
    return ConfigService(
        session=mock_session,
        repo_config_repo=mock_repo_config_repo,
        developer_profile_repo=mock_dev_repo,
    )


# ------------------------------------------------------------------
# enroll_repo
# ------------------------------------------------------------------


async def test_enroll_repo_returns_response(svc, mock_repo_config_repo, mock_session):
    mock_repo_config_repo.create.return_value = _make_repo_orm()
    body = RepoConfigCreate(installation_id=999, repo_full_name="org/repo")
    result = await svc.enroll_repo(body)
    assert result.repo_id == 42
    assert result.repo_full_name == "org/repo"
    mock_session.commit.assert_called_once()


async def test_enroll_repo_passes_config_dict(svc, mock_repo_config_repo):
    mock_repo_config_repo.create.return_value = _make_repo_orm()
    body = RepoConfigCreate(installation_id=999, repo_full_name="org/repo")
    await svc.enroll_repo(body)
    _, kwargs = mock_repo_config_repo.create.call_args
    assert "config" in kwargs
    assert isinstance(kwargs["config"], dict)


# ------------------------------------------------------------------
# get_repo
# ------------------------------------------------------------------


async def test_get_repo_found(svc, mock_repo_config_repo):
    mock_repo_config_repo.get_by_id.return_value = _make_repo_orm()
    result = await svc.get_repo(42)
    assert result.repo_id == 42


async def test_get_repo_not_found_raises(svc, mock_repo_config_repo):
    mock_repo_config_repo.get_by_id.return_value = None
    with pytest.raises(RepoNotFoundError):
        await svc.get_repo(99)


# ------------------------------------------------------------------
# update_repo_config
# ------------------------------------------------------------------


async def test_update_repo_config_returns_response(svc, mock_repo_config_repo, mock_session):
    mock_repo_config_repo.update_config.return_value = _make_repo_orm()
    body = RepoConfigUpdate(config=RepoConfigSettings())
    result = await svc.update_repo_config(42, body)
    assert result.repo_id == 42
    mock_session.commit.assert_called_once()


async def test_update_repo_config_not_found_raises(svc, mock_repo_config_repo):
    mock_repo_config_repo.update_config.return_value = None
    with pytest.raises(RepoNotFoundError):
        await svc.update_repo_config(99, RepoConfigUpdate(config=RepoConfigSettings()))


# ------------------------------------------------------------------
# add_developer
# ------------------------------------------------------------------


async def test_add_developer_returns_response(svc, mock_repo_config_repo, mock_dev_repo, mock_session):
    mock_repo_config_repo.get_by_id.return_value = _make_repo_orm()
    mock_dev_repo.create.return_value = _make_dev_orm()
    body = DeveloperProfileCreate(github_login="alice", skills=["bug"])
    result = await svc.add_developer(42, body)
    assert result.github_login == "alice"
    mock_session.commit.assert_called_once()


async def test_add_developer_repo_not_found_raises(svc, mock_repo_config_repo):
    mock_repo_config_repo.get_by_id.return_value = None
    with pytest.raises(RepoNotFoundError):
        await svc.add_developer(99, DeveloperProfileCreate(github_login="alice"))


async def test_add_developer_duplicate_raises(svc, mock_repo_config_repo, mock_dev_repo, mock_session):
    mock_repo_config_repo.get_by_id.return_value = _make_repo_orm()
    mock_dev_repo.create.side_effect = IntegrityError(None, None, Exception("unique"))
    with pytest.raises(DeveloperAlreadyExistsError):
        await svc.add_developer(42, DeveloperProfileCreate(github_login="alice"))
    mock_session.rollback.assert_called_once()


# ------------------------------------------------------------------
# update_developer
# ------------------------------------------------------------------


async def test_update_developer_returns_response(svc, mock_dev_repo, mock_session):
    mock_dev_repo.update.return_value = _make_dev_orm()
    body = DeveloperProfileUpdate(skills=["feature"])
    result = await svc.update_developer(42, "alice", body)
    assert result.github_login == "alice"
    mock_session.commit.assert_called_once()


async def test_update_developer_not_found_raises(svc, mock_dev_repo):
    mock_dev_repo.update.return_value = None
    with pytest.raises(DeveloperNotFoundError):
        await svc.update_developer(42, "ghost", DeveloperProfileUpdate())


# ------------------------------------------------------------------
# remove_developer
# ------------------------------------------------------------------


async def test_remove_developer_commits(svc, mock_dev_repo, mock_session):
    mock_dev_repo.delete.return_value = True
    await svc.remove_developer(42, "alice")
    mock_session.commit.assert_called_once()


async def test_remove_developer_not_found_raises(svc, mock_dev_repo):
    mock_dev_repo.delete.return_value = False
    with pytest.raises(DeveloperNotFoundError):
        await svc.remove_developer(42, "ghost")
