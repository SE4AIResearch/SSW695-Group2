from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from buma.gateway.publishers.queue import QUEUE_KEY, QueuePublisher
from buma.schemas.normalized_event import IssueRef, NormalizedEvent, RepoRef

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


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.lpush = AsyncMock()
    return r


async def test_publishes_to_correct_key(mock_redis):
    publisher = QueuePublisher(redis=mock_redis)
    await publisher.publish(_make_event())
    assert mock_redis.lpush.call_args[0][0] == QUEUE_KEY


async def test_payload_is_valid_json(mock_redis):
    publisher = QueuePublisher(redis=mock_redis)
    await publisher.publish(_make_event())
    payload_str = mock_redis.lpush.call_args[0][1]
    parsed = json.loads(payload_str)
    assert parsed["delivery_id"] == "delivery-abc"
    assert parsed["event_name"] == "issues"
    assert parsed["repo"]["full_name"] == "owner/repo"
