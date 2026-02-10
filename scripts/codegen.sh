#!/usr/bin/env bash
set -euo pipefail

echo "=== Running OpenAPI code generation ==="
if [ -f "openapi.yaml" ]; then
  uv run datamodel-codegen \
    --input openapi.yaml \
    --output src/buma/generated/models.py \
    --input-file-type openapi
  echo "=== Codegen complete ==="
else
  echo "=== No openapi.yaml found, skipping codegen ==="
fi