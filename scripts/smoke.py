#!/usr/bin/env python3
"""
Buma end-to-end smoke test — run all phases at once or step by step.

Prerequisites:
  docker compose up db -d        # Postgres must be running
  uv run alembic upgrade head    # Migrations must be applied

─────────────────────────────────────────────────────────────
Automated (all phases in one command):
  uv run python scripts/smoke.py run

Step-by-step (inspect each phase individually):
  uv run python scripts/smoke.py seed

  # In a separate terminal — keep it open:
  uv run python scripts/smoke.py gateway

  uv run python scripts/smoke.py webhook
  export SMOKE_DELIVERY_ID=<value printed above>

  uv run python scripts/smoke.py worker
  uv run python scripts/smoke.py verify
  uv run python scripts/smoke.py preview
─────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse
import asyncio
import sys

# scripts/ is on sys.path when running as `python scripts/smoke.py`
# smoke/ is therefore importable as the `smoke` package.
from dotenv import load_dotenv

load_dotenv()

# Imports must come after load_dotenv() so DATABASE_URL etc. are in the environment.
from smoke.commands import (  # noqa: E402
    cmd_gateway,
    cmd_preview,
    cmd_run,
    cmd_seed,
    cmd_verify,
    cmd_webhook,
    cmd_worker,
)

_ASYNC_COMMANDS = {
    "seed": cmd_seed,
    "worker": cmd_worker,
    "verify": cmd_verify,
    "preview": cmd_preview,
    "run": cmd_run,
}

_SYNC_COMMANDS = {
    "gateway": cmd_gateway,
    "webhook": cmd_webhook,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="smoke",
        description="Buma end-to-end smoke test.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "step-by-step usage:\n"
            "  uv run python scripts/smoke.py seed\n"
            "  uv run python scripts/smoke.py gateway      # separate terminal\n"
            "  uv run python scripts/smoke.py webhook\n"
            "  export SMOKE_DELIVERY_ID=<printed value>\n"
            "  uv run python scripts/smoke.py worker\n"
            "  uv run python scripts/smoke.py verify\n"
            "  uv run python scripts/smoke.py preview\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.add_parser("seed", help="Step 1 — seed the database (RepoConfig + DeveloperProfile)")
    subparsers.add_parser("gateway", help="Step 2 — start the gateway in the foreground (Ctrl+C to stop)")
    subparsers.add_parser("webhook", help="Step 3 — send a signed webhook; prints the SMOKE_DELIVERY_ID export line")
    subparsers.add_parser("worker", help="Step 4 — consume and process one message from the queue")
    subparsers.add_parser("verify", help="Step 5 — query and display triage results (requires SMOKE_DELIVERY_ID)")
    subparsers.add_parser("preview", help="Step 6 — show the GitHub patch preview (requires SMOKE_DELIVERY_ID)")
    subparsers.add_parser("run", help="Run all phases end-to-end in one command")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command in _SYNC_COMMANDS:
        _SYNC_COMMANDS[args.command]()
    else:
        sys.exit(asyncio.run(_ASYNC_COMMANDS[args.command]()))


if __name__ == "__main__":
    main()
