"""
CLI command implementations for the smoke test.

Each public function maps 1-to-1 to a CLI subcommand.
Infrastructure helpers (_make_session_factory, _require_delivery_id) are
private to this module — callers interact only through the cmd_* functions.
"""

from __future__ import annotations

import os
import subprocess

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from buma.core.config import get_settings
from smoke.config import ENV_DELIVERY_ID, GATEWAY_PORT, REPO_ROOT
from smoke.console import fail, info, ok, section
from smoke.database import fetch_triage_results, seed_database
from smoke.gateway import gateway_process
from smoke.reporter import report_github_patch_preview, report_triage_outcome
from smoke.webhook import build_webhook, send_webhook
from smoke.worker import process_one_message

# ---------------------------------------------------------------------------
# Infrastructure helpers
# ---------------------------------------------------------------------------


def _make_session_factory(settings):
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


def _require_delivery_id() -> str:
    delivery_id = os.environ.get(ENV_DELIVERY_ID)
    if not delivery_id:
        fail(f"{ENV_DELIVERY_ID} is not set — run 'webhook' first, then export the printed value")
    return delivery_id


# ---------------------------------------------------------------------------
# Step-by-step commands
# ---------------------------------------------------------------------------


async def cmd_seed() -> None:
    """Step 1 — seed the database with RepoConfig + DeveloperProfile."""
    settings = get_settings()
    engine, session_factory = _make_session_factory(settings)
    try:
        section(1, "Seeding database")
        await seed_database(session_factory)
    finally:
        await engine.dispose()


def cmd_gateway() -> None:
    """Step 2 — start the gateway in the foreground (Ctrl+C to stop)."""
    section(2, "Starting gateway (uvicorn :8000)  —  Ctrl+C to stop")
    subprocess.run(
        [
            "uv",
            "run",
            "uvicorn",
            "buma.gateway.app:app",
            "--port",
            str(GATEWAY_PORT),
            "--log-level",
            "info",
        ],
        cwd=str(REPO_ROOT),
    )


def cmd_webhook() -> None:
    """Step 3 — send a signed webhook to the gateway and print the delivery ID."""
    settings = get_settings()
    section(3, "Sending signed POST /webhook/github")
    delivery_id, payload = build_webhook()
    send_webhook(delivery_id, payload, settings)
    ok(f"Issue title: \"{payload['issue']['title']}\"")
    print()
    print("  Copy and run the following before the next step:")
    print(f"  export {ENV_DELIVERY_ID}={delivery_id}")


async def cmd_worker() -> None:
    """Step 4 — consume and process one message from the queue."""
    settings = get_settings()
    engine, session_factory = _make_session_factory(settings)
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        section(4, "Running worker (consume one message)")
        await process_one_message(session_factory, redis_client)
    finally:
        await redis_client.aclose()
        await engine.dispose()


async def cmd_verify() -> None:
    """Step 5 — query and display the triage results from the database."""
    delivery_id = _require_delivery_id()
    settings = get_settings()
    engine, session_factory = _make_session_factory(settings)
    try:
        section(5, "Verifying database records")
        results = await fetch_triage_results(session_factory, delivery_id)
        report_triage_outcome(results)
    finally:
        await engine.dispose()


async def cmd_preview() -> None:
    """Step 6 — show the GitHub patch that would have been applied."""
    delivery_id = _require_delivery_id()
    settings = get_settings()
    engine, session_factory = _make_session_factory(settings)
    try:
        section(6, "GitHub patch preview (Phase 6 skipped — no App credentials)")
        results = await fetch_triage_results(session_factory, delivery_id)
        if not results.decision:
            fail("No TriageDecision found — run 'verify' first to check pipeline state")
        report_github_patch_preview(results.decision)
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# Automated command (all phases)
# ---------------------------------------------------------------------------


async def cmd_run() -> None:
    """Run all phases end-to-end in one command."""
    settings = get_settings()
    engine, session_factory = _make_session_factory(settings)
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
            send_webhook(delivery_id, payload, settings)
            ok(f"Issue title: \"{payload['issue']['title']}\"")

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
