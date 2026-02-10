#!/usr/bin/env bash
set -euo pipefail

echo "=== Running pytest ==="
uv run pytest tests/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v

echo "=== Tests passed ==="