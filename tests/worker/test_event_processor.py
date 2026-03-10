from __future__ import annotations

from datetime import UTC, datetime

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


async def test_process_completes_without_error():
    processor = EventProcessorService()
    await processor.process(_make_event())

async def test_process_accepts_event_with_labels():
    event = _make_event()
    object.__setattr__(event.issue, "labels", ["bug", "p1"])
    processor = EventProcessorService()
    await processor.process(event)
