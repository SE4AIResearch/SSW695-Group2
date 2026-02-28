from __future__ import annotations

from unittest.mock import AsyncMock

from buma.gateway.deps import _engine, _session_factory, get_ingest_service
from buma.gateway.services.ingest import IngestService

TEST_DB_URL = "postgresql+psycopg://test:test@localhost/test"


def test_engine_returns_same_instance_for_same_url():
    _engine.cache_clear()
    e1 = _engine(TEST_DB_URL)
    e2 = _engine(TEST_DB_URL)
    assert e1 is e2
    _engine.cache_clear()


def test_session_factory_returns_same_instance_for_same_url():
    _engine.cache_clear()
    _session_factory.cache_clear()
    f1 = _session_factory(TEST_DB_URL)
    f2 = _session_factory(TEST_DB_URL)
    assert f1 is f2
    _engine.cache_clear()
    _session_factory.cache_clear()


async def test_get_ingest_service_returns_ingest_service():
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    service = await get_ingest_service(db=mock_db, redis=mock_redis)
    assert isinstance(service, IngestService)
