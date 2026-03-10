from __future__ import annotations

import asyncio
import logging
from json import JSONDecodeError

import redis.asyncio as aioredis
from pydantic import ValidationError

from buma.gateway.publishers.queue import QUEUE_KEY
from buma.schemas.normalized_event import NormalizedEvent
from buma.worker.services.event_processor import EventProcessorService

logger = logging.getLogger(__name__)

_BRPOP_TIMEOUT = 5


class QueueConsumer:
    def __init__(self, redis: aioredis.Redis, processor: EventProcessorService) -> None:
        self._redis = redis
        self._processor = processor

    async def run_once(self) -> bool:
        """
        Pop one message from the queue and process it.

        Returns True  — a message was popped (valid or malformed).
        Returns False — timeout elapsed, queue was empty.
        """
        result = await self._redis.brpop(QUEUE_KEY, timeout=_BRPOP_TIMEOUT)
        if result is None:
            return False

        _, raw = result

        try:
            event = NormalizedEvent.model_validate_json(raw)
        except (ValidationError, JSONDecodeError):
            logger.error("Dropping malformed message (first 200 chars): %.200s", raw)
            return True

        await self._processor.process(event)
        return True

    async def run_forever(self, *, stop_event: asyncio.Event | None = None) -> None:
        """
        Loop continuously until stop_event is set (or forever if stop_event is None).
        Unhandled errors from run_once are logged and the loop continues.
        """
        logger.info("Queue consumer started on key '%s'", QUEUE_KEY)
        while stop_event is None or not stop_event.is_set():
            try:
                await self.run_once()
            except Exception:
                logger.exception("Unhandled error in consumer loop — continuing")
        logger.info("Queue consumer stopped.")
