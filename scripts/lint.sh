#!/usr/bin/env bash
set -euo pipefail

echo "=== Running ruff linter ==="
uv run ruff check .

echo "=== Checking black formatting ==="
uv run black --check .

echo "=== Lint passed ==="