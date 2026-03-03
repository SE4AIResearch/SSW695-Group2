from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from buma.gateway.repositories.webhook_delivery import WebhookDeliveryRepository

RECEIVED_AT = datetime(2024, 1, 1, tzinfo=UTC)

KWARGS = {
    "delivery_id": "delivery-abc",
    "event_name": "issues",
    "action": "opened",
    "installation_id": 12345,
    "repo_id": 111,
    "repo_full_name": "owner/repo",
    "received_at": RECEIVED_AT,
}


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    return session


async def test_insert_if_new_returns_true(mock_session):
    repo = WebhookDeliveryRepository(session=mock_session)
    result = await repo.insert_if_new(**KWARGS)
    assert result is True
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


async def test_duplicate_delivery_returns_false(mock_session):
    mock_session.flush.side_effect = IntegrityError(None, None, Exception("unique violation"))
    repo = WebhookDeliveryRepository(session=mock_session)
    result = await repo.insert_if_new(**KWARGS)
    assert result is False
    mock_session.rollback.assert_called_once()
