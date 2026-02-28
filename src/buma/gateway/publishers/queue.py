from __future__ import annotations

import redis.asyncio as aioredis

from buma.schemas.normalized_event import NormalizedEvent

QUEUE_KEY = "buma:triage:queue"


class QueuePublisher:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def publish(self, event: NormalizedEvent) -> None:
        await self._redis.lpush(QUEUE_KEY, event.model_dump_json())
