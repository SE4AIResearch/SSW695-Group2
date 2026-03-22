"""
Gateway lifecycle management for the smoke test.

Provides a context manager that starts the gateway as a background process,
waits for it to become healthy, and guarantees it is terminated on exit.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import time
from collections.abc import Generator

import httpx

from smoke.config import GATEWAY_PORT, GATEWAY_STARTUP_TIMEOUT, GATEWAY_URL, REPO_ROOT
from smoke.console import fail, ok


@contextlib.contextmanager
def gateway_process() -> Generator[None, None, None]:
    """
    Start the gateway as a background process and yield once it is healthy.
    Terminates the process on exit regardless of success or failure.

    Usage:
        with gateway_process():
            # gateway is running and healthy here
            ...
        # gateway has been terminated here
    """
    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "buma.gateway.app:app",
            "--port",
            str(GATEWAY_PORT),
            "--log-level",
            "warning",
        ],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        if not _wait_until_healthy():
            proc.terminate()
            fail(f"Gateway did not become healthy within {GATEWAY_STARTUP_TIMEOUT} s")
        ok(f"Gateway healthy — {GATEWAY_URL}/health")
        yield
    finally:
        proc.terminate()
        proc.wait()


def _wait_until_healthy() -> bool:
    """Poll /health until the gateway responds 200 or the timeout expires."""
    deadline = time.time() + GATEWAY_STARTUP_TIMEOUT
    while time.time() < deadline:
        try:
            if httpx.get(f"{GATEWAY_URL}/health", timeout=1.0).status_code == 200:
                return True
        except httpx.TransportError:
            time.sleep(0.5)
    return False
