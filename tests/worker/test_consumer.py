from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from buma.gateway.publishers.queue import QUEUE_KEY
from buma.schemas.normalized_event import IssueRef, NormalizedEvent, RepoRef
from buma.worker.consumer import QueueConsumer
from buma.worker.services.event_processor import EventProcessorService

RECEIVED_AT = datetime(2024, 1, 1, tzinfo=UTC)


def _make_event(delivery_id: str = "delivery-abc") -> NormalizedEvent:
    return NormalizedEvent(
        event_id=delivery_id,
        delivery_id=delivery_id,
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
    r.brpop = AsyncMock(return_value=None)
    return r


@pytest.fixture
def mock_processor():
    p = AsyncMock(spec=EventProcessorService)
    p.process = AsyncMock()
    return p


@pytest.fixture
def consumer(mock_redis, mock_processor):
    return QueueConsumer(redis=mock_redis, processor=mock_processor)


async def test_run_once_returns_false_on_timeout(consumer, mock_redis):
    mock_redis.brpop.return_value = None
    result = await consumer.run_once()
    assert result is False
    mock_redis.brpop.assert_called_once_with(QUEUE_KEY, timeout=5)


async def test_run_once_processes_valid_message(consumer, mock_redis, mock_processor):
    event = _make_event()
    mock_redis.brpop.return_value = (QUEUE_KEY, event.model_dump_json())
    result = await consumer.run_once()
    assert result is True
    mock_processor.process.assert_called_once()
    processed: NormalizedEvent = mock_processor.process.call_args[0][0]
    assert processed.delivery_id == "delivery-abc"
    assert processed.issue.number == 1


async def test_run_once_drops_malformed_json(consumer, mock_redis, mock_processor):
    mock_redis.brpop.return_value = (QUEUE_KEY, "not-valid-json{{{")
    result = await consumer.run_once()
    assert result is True
    mock_processor.process.assert_not_called()


async def test_run_once_drops_invalid_schema(consumer, mock_redis, mock_processor):
    mock_redis.brpop.return_value = (QUEUE_KEY, json.dumps({"unexpected": "fields"}))
    result = await consumer.run_once()
    assert result is True
    mock_processor.process.assert_not_called()


async def test_run_forever_exits_when_stop_event_is_set(consumer, mock_redis):
    stop_event = asyncio.Event()
    stop_event.set()
    await consumer.run_forever(stop_event=stop_event)
    mock_redis.brpop.assert_not_called()


async def test_run_forever_continues_after_processor_error(consumer, mock_redis, mock_processor):
    stop_event = asyncio.Event()
    event = _make_event()
    call_count = 0

    async def brpop_side_effect(key, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return (QUEUE_KEY, event.model_dump_json())
        stop_event.set()
        return None

    mock_redis.brpop.side_effect = brpop_side_effect
    mock_processor.process.side_effect = RuntimeError("triage exploded")

    await consumer.run_forever(stop_event=stop_event)
    assert call_count >= 2


async def test_run_forever_processes_multiple_messages(consumer, mock_redis, mock_processor):
    stop_event = asyncio.Event()
    events = [_make_event(f"delivery-{i}") for i in range(3)]
    call_count = 0

    async def brpop_side_effect(key, timeout):
        nonlocal call_count
        if call_count < len(events):
            msg = events[call_count].model_dump_json()
            call_count += 1
            return (QUEUE_KEY, msg)
        stop_event.set()
        return None

    mock_redis.brpop.side_effect = brpop_side_effect
    await consumer.run_forever(stop_event=stop_event)
    assert mock_processor.process.call_count == 3

