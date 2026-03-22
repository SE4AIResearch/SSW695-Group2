"""
Smoke test configuration — all constants in one place.
Change these to point the smoke test at a different repo or developer.
"""

from pathlib import Path

# Repository enrolled in buma for this smoke test
REPO_ID = 123456789
REPO_FULL_NAME = "smoke-org/smoke-repo"
INSTALLATION_ID = 99001

# Developer profile that should receive the test assignment
DEVELOPER_LOGIN = "emmanuel"

# GitHub issue used in the test payload
ISSUE_NUMBER = 42

# Gateway settings
GATEWAY_PORT = 8000
GATEWAY_URL = f"http://localhost:{GATEWAY_PORT}"
GATEWAY_STARTUP_TIMEOUT = 15  # seconds

# A second repo_id used only to seed dave's profile, proving cross-repo isolation
OTHER_REPO_ID = 999999999

# Absolute path to the repository root (scripts/smoke/config.py → up three levels)
REPO_ROOT = Path(__file__).parent.parent.parent

# Environment variable used to pass delivery_id between step-by-step CLI commands
ENV_DELIVERY_ID = "SMOKE_DELIVERY_ID"
