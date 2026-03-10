from __future__ import annotations

import asyncio
import logging
import signal

import redis.asyncio as aioredis

from buma.core.config import get_settings
from buma.worker.consumer import QueueConsumer
from buma.worker.services.event_processor import EventProcessorService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        processor = EventProcessorService()
        consumer = QueueConsumer(redis=redis_client, processor=processor)
        await consumer.run_forever(stop_event=stop_event)
    finally:
        await redis_client.aclose()
        logger.info("Redis connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
