from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from buma.gateway.publishers.queue import QueuePublisher
from buma.gateway.repositories.webhook_delivery import WebhookDeliveryRepository
from buma.gateway.services.ingest import IngestResult, IngestService
from buma.schemas.normalized_event import NormalizedEvent

RECEIVED_AT = datetime(2024, 1, 1, tzinfo=UTC)
DELIVERY_ID = "delivery-abc"

ISSUE_PAYLOAD = {
    "action": "opened",
    "installation": {"id": 12345},
    "repository": {"id": 111, "full_name": "owner/repo", "private": False},
    "issue": {
        "number": 1,
        "id": 999,
        "node_id": "I_node",
        "url": "https://api.github.com/repos/owner/repo/issues/1",
        "html_url": "https://github.com/owner/repo/issues/1",
        "title": "Bug",
        "body": "Description",
        "labels": [{"name": "bug"}],
        "user": {"login": "octocat"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    },
    "sender": {"login": "octocat"},
}


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_repo():
    repo = AsyncMock(spec=WebhookDeliveryRepository)
    repo.insert_if_new = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_publisher():
    publisher = AsyncMock(spec=QueuePublisher)
    publisher.publish = AsyncMock()
    return publisher


@pytest.fixture
def service(mock_session, mock_repo, mock_publisher):
    return IngestService(session=mock_session, repo=mock_repo, publisher=mock_publisher)


async def test_ignored_if_not_issues_event(service, mock_repo):
    result = await service.handle(
        delivery_id=DELIVERY_ID, event_name="push", payload=ISSUE_PAYLOAD, received_at=RECEIVED_AT
    )
    assert result == IngestResult.IGNORED
    mock_repo.insert_if_new.assert_not_called()


async def test_ignored_if_action_not_opened(service, mock_repo):
    result = await service.handle(
        delivery_id=DELIVERY_ID,
        event_name="issues",
        payload={**ISSUE_PAYLOAD, "action": "closed"},
        received_at=RECEIVED_AT,
    )
    assert result == IngestResult.IGNORED
    mock_repo.insert_if_new.assert_not_called()


async def test_duplicate_if_not_new(service, mock_repo, mock_publisher, mock_session):
    mock_repo.insert_if_new.return_value = False
    result = await service.handle(
        delivery_id=DELIVERY_ID, event_name="issues", payload=ISSUE_PAYLOAD, received_at=RECEIVED_AT
    )
    assert result == IngestResult.DUPLICATE
    mock_publisher.publish.assert_not_called()
    mock_session.commit.assert_not_called()


async def test_queued_publishes_and_commits(service, mock_publisher, mock_session):
    result = await service.handle(
        delivery_id=DELIVERY_ID, event_name="issues", payload=ISSUE_PAYLOAD, received_at=RECEIVED_AT
    )
    assert result == IngestResult.QUEUED
    mock_publisher.publish.assert_called_once()
    mock_session.commit.assert_called_once()


async def test_normalized_event_fields(service, mock_publisher):
    await service.handle(delivery_id=DELIVERY_ID, event_name="issues", payload=ISSUE_PAYLOAD, received_at=RECEIVED_AT)
    event: NormalizedEvent = mock_publisher.publish.call_args[0][0]
    assert event.delivery_id == DELIVERY_ID
    assert event.event_id == DELIVERY_ID
    assert event.repo.full_name == "owner/repo"
    assert event.issue.number == 1
    assert event.issue.labels == ["bug"]
    assert event.sender_login == "octocat"
