"""
Console output helpers used throughout the smoke test.

All output is routed through these functions so the visual style is
consistent and easy to change in one place.
"""

import sys


def section(n: int, label: str) -> None:
    """Print a numbered step header."""
    print(f"\n{'─' * 60}")
    print(f"  Step {n}: {label}")
    print(f"{'─' * 60}")


def ok(msg: str) -> None:
    """Print a success line."""
    print(f"  ✓  {msg}")


def info(msg: str) -> None:
    """Print an informational detail line."""
    print(f"  ·  {msg}")


def fail(msg: str) -> None:
    """Print a failure line and exit with a non-zero code."""
    print(f"  ✗  {msg}")
    sys.exit(1)
