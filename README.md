# buma — Intelligent Bug Triaging & Assignment System

Tagline: **a reliable first responder for new GitHub issues**.

buma is a capstone project that automates the first step of bug triage in GitHub:

- Ingest new issue events (securely and reliably)
- Classify bug category and set priority (rules-first baseline)
- Assign the best-fit developer using team **skills + capacity**
- Apply labels, set assignee, and post an **explanation comment** (transparent + auditable)
- Persist a decision log for analytics and continuous improvement

## Project goals (semester MVP)

The MVP (P0) focuses on a reliable end-to-end workflow before “smart but fragile” intelligence:

- Webhook ingestion + validation (issue opened)
- Triage engine (rule-based baseline): category + priority
- Assignee selection using skills + capacity + tie-break rules
- GitHub updates: labels + assignee + explanation comment
- Decision log persisted for auditability
- Dashboard: configuration + triage history + workload view

Optional (P1, only if it does not reduce P0 reliability): manual overrides, confidence + fallback path, lightweight offline-trained ML category classifier, and more analytics.

## Repository status

The P0 pipeline is fully implemented and smoke-tested locally:

- Gateway (`src/buma/gateway/`) — webhook ingest, HMAC validation, Redis publish; dashboard config + observability API endpoints
- Worker (`src/buma/worker/`) — queue consumer, triage engine, assignee selector, DB persistence, GitHub patch
- Database (`src/buma/db/`) — all 6 ORM models, Alembic migration applied
- API schemas (`src/buma/schemas/api/`) — typed request/response schemas for all `/api/*` routes
- Unit tests (`tests/`) + end-to-end smoke test (`scripts/smoke.py`)
- Devcontainer for a consistent toolchain (`.devcontainer/`)

Remaining P0 work: GitHub OAuth 2.0 (dashboard login + session auth on API routes); public HTTPS endpoint; Dashboard UI (owned by UI team).

## High-level architecture (target)

GitHub issue events flow through a reliable pipeline:

`GitHub → Webhook ingest API → Queue → Triage worker → DB → Dashboard`

The queue enables retries and burst protection; the decision log enables traceability and metrics.

## Getting started

### Option A: Devcontainer (recommended)

Prerequisites:

- Docker
- VS Code + the “Dev Containers” extension

Steps:

1. Open this repository in VS Code.
2. Run **Dev Containers: Reopen in Container**.
3. Wait for `uv sync --dev` to finish (runs automatically via `postCreateCommand`).

Then run:

```bash
./scripts/lint.sh
./scripts/test.sh
./scripts/codegen.sh
```

### Option B: Local setup with `uv`

Prerequisites:

- Python 3.11+
- `uv`

```bash
uv sync --dev
./scripts/lint.sh
./scripts/test.sh
./scripts/codegen.sh
```

## Running the services

Before starting any service, bring up the infrastructure and apply migrations:

```bash
docker compose up db -d          # PostgreSQL on :5432 and Redis on :6379
uv run alembic upgrade head      # apply DB migrations
```

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
# then edit .env — minimum required:
# DATABASE_URL, REDIS_URL, GITHUB_WEBHOOK_SECRET
```

### Gateway (webhook ingest + dashboard API)

```bash
uv run uvicorn buma.gateway.app:app --reload --port 8000
```

Available routes:
- `GET  /health` — liveness check
- `POST /webhook/github` — GitHub webhook receiver
- `POST|GET|PATCH /api/config/repos` — repo enrollment and config
- `POST|PATCH|DELETE /api/config/repos/{id}/developers` — developer profile management
- `GET  /api/triage/{repo_id}` — triage decision history
- `GET  /api/workload/{repo_id}` — developer workload view

### Worker (triage pipeline)

In a second terminal:

```bash
uv run python -m buma.worker.runner
```

The worker connects to Redis, polls `buma:triage:queue`, and processes events through the full triage pipeline (classify → assign → persist → patch GitHub). It shuts down cleanly on `Ctrl+C` or `SIGTERM` — it finishes the current message before exiting.

### CORS (for the Dashboard UI)

The gateway allows cross-origin requests from the origins listed in `CORS_ORIGINS` (comma-separated). The default covers local UI development:

```bash
# in .env:
CORS_ORIGINS=http://localhost:5173
```

For production, set it to the deployed UI origin:

```bash
CORS_ORIGINS=https://buma.example.com
```

Multiple origins are supported:

```bash
CORS_ORIGINS=https://buma.example.com,http://localhost:5173
```

### Optional: GitHub App credentials (for Phase 6 — live GitHub patching)

Without these, the worker runs Phases 1–5 only (`patch_state` stays `DECIDED`):

```bash
# in .env:
GITHUB_APP_ID=<your app id>
GITHUB_APP_PRIVATE_KEY=<PEM content with \n for newlines>
```

## Scripts (the contract)

Local development and CI should run the same scripts (avoid duplicating logic in workflow YAML).

- `scripts/lint.sh`: `ruff` lint + `black --check`
- `scripts/test.sh`: `pytest` + coverage gate
- `scripts/codegen.sh`: OpenAPI model generation (skips if `openapi.yaml` is not present)
- `scripts/smoke.py`: end-to-end local smoke test (Phases 1–5)

### Running the smoke test

Prerequisites:
```bash
docker compose up db -d          # Postgres and Redis must be running
uv run alembic upgrade head      # Migrations must be applied
```

Automated (all phases in one command):
```bash
uv run python scripts/smoke.py run
```

Step-by-step (inspect each phase individually):
```bash
uv run python scripts/smoke.py seed
uv run python scripts/smoke.py gateway      # separate terminal — Ctrl+C to stop
uv run python scripts/smoke.py webhook
export SMOKE_DELIVERY_ID=<value printed above>
uv run python scripts/smoke.py worker
uv run python scripts/smoke.py verify
uv run python scripts/smoke.py preview
```

API endpoints smoke test (config + observability routes against a live gateway):
```bash
uv run python scripts/smoke.py api
```

> Do not run as `./scripts/smoke.py` — the shebang does not resolve to the uv virtualenv.

## Repository layout

- `src/buma/`: Python package
- `tests/`: test suite
- `scripts/`: lint/test/codegen scripts
- `.devcontainer/`: reproducible dev environment
- `.github/ISSUE_TEMPLATE/`: Epic/Feature/User Story templates
- `contributors/`: lightweight “who’s on the team” notes

## Contributing

### Workflow

- Create or pick up work via GitHub issues (use the templates).
- Create a feature branch and open a PR.
- Keep PRs small and focused (one behavioral change per PR when possible).
- Run the scripts locally before requesting review:

```bash
./scripts/lint.sh # uv run ruff check . --fix | uv run ruff format .
./scripts/test.sh
./scripts/codegen.sh
```

### Code quality

- Formatting: `black` (line length 120)
- Linting: `ruff`
- Tests: `pytest` (coverage is enforced by `scripts/test.sh`)

### Dependencies

- Add Python deps to `pyproject.toml`.
- Update the lockfile with `uv lock` and commit `uv.lock`.

### Scope guardrails

The capstone success criterion is “**works every time**” for the P0 pipeline.

- Prioritize reliability, idempotency, and debuggability over adding new features.
- Don’t merge P1/roadmap work if it reduces P0 stability.
- Add one major capability at a time; validate end-to-end before layering more.

### Secrets and security

- Never commit secrets (`.env`, credentials, private keys).
- Prefer environment variables / secret managers for local + CI.

### Adding yourself (optional)

Add a short file under `contributors/` (example: `contributors/your-name.md`) with your name, role, and GitHub handle.

## Resources
- GitHub Webhooks: https://docs.github.com/webhooks
- Validating Github Webhook payloads: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
- HMAC verification: https://docs.github.com/webhooks/securing-your-webhooks#validating-payloads-from-github
- Python HMAC: https://docs.python.org/3/library/hmac.html
- Python hashlib: https://docs.python.org/3/library/hashlib

## Example of Webhook Delivery from GitHub

```text
> POST /payload HTTP/1.1

> X-GitHub-Delivery: 72d3162e-cc78-11e3-81ab-4c9367dc0958
> X-Hub-Signature: sha1=7d38cdd689735b008b3c702edd92eea23791c5f6
> X-Hub-Signature-256: sha256=d57c68ca6f92289e6987922ff26938930f6e66a2d161ef06abdf1859230aa23c
> User-Agent: GitHub-Hookshot/044aadd
> Content-Type: application/json
> Content-Length: 6615
> X-GitHub-Event: issues
> X-GitHub-Hook-ID: 292430182
> X-GitHub-Hook-Installation-Target-ID: 79929171
> X-GitHub-Hook-Installation-Target-Type: repository

> {
>   "action": "opened",
>   "issue": {
>     "url": "https://api.github.com/repos/octocat/Hello-World/issues/1347",
>     "number": 1347,
>     ...
>   },
>   "repository" : {
>     "id": 1296269,
>     "full_name": "octocat/Hello-World",
>     "owner": {
>       "login": "octocat",
>       "id": 1,
>       ...
>     },
>     ...
>   },
>   "sender": {
>     "login": "octocat",
>     "id": 1,
>     ...
>   }
> }
```

## License

A project license has not been added yet. Do not assume reuse permissions until a `LICENSE` file is present.
