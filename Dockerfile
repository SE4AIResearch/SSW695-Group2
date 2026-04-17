FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first — this layer is cached unless pyproject.toml/uv.lock changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install the project itself
COPY README.md ./
COPY src/ ./src/
RUN rm -rf src/*.egg-info
COPY migrations/ ./migrations/
COPY alembic.ini ./
RUN uv sync --frozen --no-dev --no-editable

# Run as non-root
RUN useradd --system --create-home buma
USER buma