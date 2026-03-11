from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from buma.db.models import RepoConfig
from buma.schemas.normalized_event import IssueRef, NormalizedEvent, RepoRef
from buma.worker.services.event_processor import EventProcessorService

RECEIVED_AT = datetime(2024, 1, 1, tzinfo=UTC)


def _make_event() -> NormalizedEvent:
    return NormalizedEvent(
        event_id="delivery-abc",
        delivery_id="delivery-abc",
        event_name="issues",
        action="opened",
        received_at=RECEIVED_AT,
        installation_id=12345,
        repo=RepoRef(id=111, full_name="owner/repo", private=False),
        issue=IssueRef(
            number=1,
            id=999,
            node_id="I_node",
            url="https://api.github.com/repos/owner/repo/issues/1",
            html_url="https://github.com/owner/repo/issues/1",
            title="Bug",
            body=None,
            labels=[],
            author_login="octocat",
            created_at=RECEIVED_AT,
            updated_at=RECEIVED_AT,
        ),
    )


def _make_processor(repo_config: RepoConfig | None) -> EventProcessorService:
    """Build an EventProcessorService with a mocked session_factory."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=repo_config)))
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_factory = MagicMock(return_value=mock_session)
    return EventProcessorService(session_factory=mock_factory)


async def test_process_skips_when_repo_not_enrolled():
    processor = _make_processor(repo_config=None)
    # Should return early without raising
    await processor.process(_make_event())


async def test_process_continues_when_repo_enrolled():
    config = MagicMock(spec=RepoConfig)
    processor = _make_processor(repo_config=config)
    await processor.process(_make_event())


async def test_process_accepts_event_with_labels():
    config = MagicMock(spec=RepoConfig)
    processor = _make_processor(repo_config=config)
    event = _make_event()
    object.__setattr__(event.issue, "labels", ["bug", "p1"])
    await processor.process(event)
