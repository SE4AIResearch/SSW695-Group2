from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from buma.db.models import DeveloperProfile
from buma.worker.services.assignee_selector import AssigneeSelector


def _make_dev(
    id: int,
    github_login: str,
    skills: list[str],
    open_assignments: int = 0,
    max_capacity: int = 5,
    version: int = 0,
) -> DeveloperProfile:
    dev = MagicMock(spec=DeveloperProfile)
    dev.id = id
    dev.github_login = github_login
    dev.skills = skills
    dev.open_assignments = open_assignments
    dev.max_capacity = max_capacity
    dev.version = version
    return dev


def _make_session(candidates: list[DeveloperProfile], update_rowcounts: list[int] | None = None) -> AsyncMock:
    """
    Build a mock AsyncSession.
    - First execute() call returns the candidate query result.
    - Subsequent execute() calls return update results with the given rowcounts (default: all 1).
    """
    if update_rowcounts is None:
        update_rowcounts = [1] * len(candidates)

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = candidates

    query_result = MagicMock()
    query_result.scalars.return_value = scalars_mock

    update_results = [MagicMock(rowcount=rc) for rc in update_rowcounts]

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=[query_result] + update_results)
    session.flush = AsyncMock()
    return session


@pytest.fixture
def selector() -> AssigneeSelector:
    return AssigneeSelector()


# ---------------------------------------------------------------------------
# No candidates
# ---------------------------------------------------------------------------


async def test_returns_none_when_no_developers(selector: AssigneeSelector) -> None:
    session = _make_session(candidates=[])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result is None


async def test_returns_none_when_no_skill_match(selector: AssigneeSelector) -> None:
    dev = _make_dev(id=1, github_login="alice", skills=["feature", "docs"])
    session = _make_session(candidates=[dev])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result is None


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_returns_login_on_skill_and_capacity_match(selector: AssigneeSelector) -> None:
    dev = _make_dev(id=1, github_login="alice", skills=["bug"])
    session = _make_session(candidates=[dev], update_rowcounts=[1])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result == "alice"


async def test_flush_is_called_after_update(selector: AssigneeSelector) -> None:
    dev = _make_dev(id=1, github_login="alice", skills=["bug"])
    session = _make_session(candidates=[dev], update_rowcounts=[1])
    await selector.select(session, repo_id=1, category="bug")
    session.flush.assert_awaited_once()


# ---------------------------------------------------------------------------
# Optimistic locking — version conflict
# ---------------------------------------------------------------------------


async def test_skips_candidate_on_version_conflict(selector: AssigneeSelector) -> None:
    dev_a = _make_dev(id=1, github_login="alice", skills=["bug"], open_assignments=1)
    dev_b = _make_dev(id=2, github_login="bob", skills=["bug"], open_assignments=2)
    # alice's UPDATE returns 0 rows (conflict), bob's returns 1
    session = _make_session(candidates=[dev_a, dev_b], update_rowcounts=[0, 1])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result == "bob"


async def test_returns_none_when_all_candidates_conflict(selector: AssigneeSelector) -> None:
    dev_a = _make_dev(id=1, github_login="alice", skills=["bug"])
    dev_b = _make_dev(id=2, github_login="bob", skills=["bug"])
    session = _make_session(candidates=[dev_a, dev_b], update_rowcounts=[0, 0])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result is None


async def test_flush_called_once_per_update_attempt(selector: AssigneeSelector) -> None:
    dev_a = _make_dev(id=1, github_login="alice", skills=["bug"])
    dev_b = _make_dev(id=2, github_login="bob", skills=["bug"])
    # alice conflicts, bob succeeds — two UPDATE attempts, two flushes
    session = _make_session(candidates=[dev_a, dev_b], update_rowcounts=[0, 1])
    await selector.select(session, repo_id=1, category="bug")
    assert session.flush.await_count == 2


# ---------------------------------------------------------------------------
# Candidate ordering
# ---------------------------------------------------------------------------


async def test_prefers_least_loaded_candidate(selector: AssigneeSelector) -> None:
    # DB query returns ordered by open_assignments ASC — selector takes first eligible
    dev_light = _make_dev(id=1, github_login="alice", skills=["bug"], open_assignments=1)
    dev_heavy = _make_dev(id=2, github_login="bob", skills=["bug"], open_assignments=4)
    session = _make_session(candidates=[dev_light, dev_heavy], update_rowcounts=[1])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result == "alice"


# ---------------------------------------------------------------------------
# Skills matching
# ---------------------------------------------------------------------------


async def test_skills_match_is_exact(selector: AssigneeSelector) -> None:
    # "bug" must be an element of skills, not a substring
    dev = _make_dev(id=1, github_login="alice", skills=["bugfix"])
    session = _make_session(candidates=[dev])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result is None


async def test_developer_with_multiple_skills_matches(selector: AssigneeSelector) -> None:
    dev = _make_dev(id=1, github_login="alice", skills=["feature", "bug", "docs"])
    session = _make_session(candidates=[dev], update_rowcounts=[1])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result == "alice"


async def test_skips_non_matching_dev_picks_next_matching(selector: AssigneeSelector) -> None:
    dev_wrong = _make_dev(id=1, github_login="alice", skills=["feature"])
    dev_right = _make_dev(id=2, github_login="bob", skills=["bug"])
    session = _make_session(candidates=[dev_wrong, dev_right], update_rowcounts=[1])
    result = await selector.select(session, repo_id=1, category="bug")
    assert result == "bob"
