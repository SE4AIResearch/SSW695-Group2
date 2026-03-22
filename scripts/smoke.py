#!/usr/bin/env python3
"""
Buma end-to-end smoke test — validates the full Phases 1–5 pipeline locally.

What it does:
  1. Seeds the database with a RepoConfig + DeveloperProfile
  2. Starts the gateway (uvicorn on :8000) as a background process
  3. Sends a signed POST /webhook/github (exactly as GitHub would)
  4. Runs the worker's consume-once loop to process the event
  5. Queries the database and reports the triage outcome
  6. Shows what would have been sent to GitHub (Phase 6 skipped — no App credentials)

Prerequisites:
  docker compose up db -d        # Postgres must be running
  uv run alembic upgrade head    # Migrations must be applied

Usage:
  uv run python scripts/smoke.py
"""

from __future__ import annotations

import asyncio
import sys

# scripts/ is on sys.path when running as `python scripts/smoke.py`
# smoke/ is therefore importable as the `smoke` package.
import redis.asyncio as aioredis
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

# Buma imports must come after load_dotenv() so DATABASE_URL etc. are in the environment.
from smoke.console import info, section  # noqa: E402
from smoke.database import fetch_triage_results, seed_database  # noqa: E402
from smoke.gateway import gateway_process  # noqa: E402
from smoke.reporter import report_github_patch_preview, report_triage_outcome  # noqa: E402
from smoke.webhook import build_webhook, send_webhook  # noqa: E402
from smoke.worker import process_one_message  # noqa: E402

from buma.core.config import get_settings  # noqa: E402, tells the linter— suppress the warning on this line.


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    print("\n" + "═" * 60)
    print("  Buma Smoke Test — Phases 1–5")
    print("═" * 60)

    try:
        section(1, "Seeding database")
        await seed_database(session_factory)

        section(2, "Starting gateway (uvicorn :8000)")
        with gateway_process():
            section(3, "Sending signed POST /webhook/github")
            delivery_id, payload = build_webhook()
            info(f"delivery_id = {delivery_id}")
            response = send_webhook(delivery_id, payload, settings)
            info(f"Gateway response: {response}")
            info(f"Issue title: \"{payload['issue']['title']}\"")

            section(4, "Running worker (consume one message)")
            await process_one_message(session_factory, redis_client)

        section(5, "Verifying database records")
        results = await fetch_triage_results(session_factory, delivery_id)
        report_triage_outcome(results)

        section(6, "GitHub patch preview (Phase 6 skipped — no App credentials)")
        report_github_patch_preview(results.decision)

        print("\n" + "═" * 60)
        print("  SMOKE TEST PASSED ✓")
        print("═" * 60 + "\n")

    finally:
        await redis_client.aclose()
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
