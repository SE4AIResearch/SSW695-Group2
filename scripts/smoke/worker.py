"""
Worker lifecycle for the smoke test.

Responsibilities:
  - process_one_message: spin up a QueueConsumer, consume exactly one event from
    the Redis queue, and verify it was processed successfully
"""

from __future__ import annotations

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from buma.worker.consumer import QueueConsumer
from buma.worker.services.event_processor import EventProcessorService
from smoke.console import fail, ok


async def process_one_message(
    session_factory: async_sessionmaker[AsyncSession],
    redis_client: aioredis.Redis,
) -> None:
    """Run the worker's consume-once loop to process exactly one queued event."""
    processor = EventProcessorService(session_factory=session_factory)
    consumer = QueueConsumer(redis=redis_client, processor=processor)
    processed = await consumer.run_once()
    if not processed:
        fail("Worker timed out — message not found in queue")
    ok("Worker consumed and processed the message")
