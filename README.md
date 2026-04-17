# buma — Intelligent Bug Triaging & Assignment System

**A reliable first responder for new GitHub issues.**

buma automates the first step of bug triage in GitHub:

- Ingest new issue events securely and reliably
- Classify bug category and set priority (rules-first baseline)
- Assign the best-fit developer using team **skills + capacity**
- Apply labels, set assignee, and post an **explanation comment** (transparent + auditable)
- Persist a decision log for analytics and continuous improvement

## Project goals (semester MVP)

The MVP (P0) focuses on a reliable end-to-end workflow before "smart but fragile" intelligence:

- Webhook ingestion + validation (issue opened)
- Triage engine (rule-based baseline): category + priority
- Assignee selection using skills + capacity + tie-break rules
- GitHub updates: labels + assignee + explanation comment
- Decision log persisted for auditability
- Dashboard: configuration + triage history + workload view

Optional (P1, only if it does not reduce P0 reliability): manual overrides, confidence + fallback path, lightweight offline-trained ML category classifier, and more analytics.

## Repository status

The full P0 backend pipeline is implemented and smoke-tested:

- Gateway (`src/buma/gateway/`) — webhook ingest, HMAC validation, Redis publish; dashboard config + observability API; GitHub OAuth 2.0 login + session auth
- Worker (`src/buma/worker/`) — queue consumer, triage engine, assignee selector, DB persistence, GitHub patch (labels + assignee + comment)
- Database (`src/buma/db/`) — all 6 ORM models, Alembic migration applied
- API schemas (`src/buma/schemas/api/`) — typed request/response schemas for all `/api/*` routes
- Unit tests (`tests/`) + end-to-end smoke test (`scripts/smoke.py`)
- Devcontainer for a consistent toolchain (`.devcontainer/`)

Remaining P0 work: public HTTPS endpoint + webhook registration; Dashboard UI (owned by UI team).

## High-level architecture

```
GitHub → Webhook ingest API → Redis Queue → Triage Worker → DB → Dashboard
```

The queue enables retries and burst protection. The decision log enables traceability and metrics.

---

## Prerequisites

- **Docker** and **Docker Compose** — required for both dev paths below
- **Python 3.11+** and **uv** — required for host dev only

Install `uv` if you don't have it:
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

---

## Environment setup

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

`.env.example`:
```bash
# Postgres credentials — used by the db service and DATABASE_URL
POSTGRES_USER=buma
POSTGRES_PASSWORD=buma
POSTGRES_DB=buma

# Database — uses Docker service name "db"
DATABASE_URL=postgresql+psycopg://buma:buma@db:5432/buma

# Redis — uses Docker service name "redis"
REDIS_URL=redis://redis:6379/0

# GitHub Webhook (from your GitHub App settings)
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# GitHub App (JWT auth for patching issues — Phase 6)
# Without these, the worker skips GitHub patching (patch_state stays DECIDED)
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=   # full PEM content, newlines as \n

# GitHub OAuth App (dashboard login)
GITHUB_OAUTH_CLIENT_ID=
GITHUB_OAUTH_CLIENT_SECRET=

# Session cookie signing — use a strong random value in production
SESSION_SECRET=dev-secret-change-in-production!

# CORS — comma-separated list of allowed origins for the dashboard UI
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Running in development

### Option A — Docker Compose (recommended)

Runs the full stack (Postgres, Redis, gateway, worker) in one command. `.env` is the single source of truth — no local Python install needed beyond Docker.

**First-time setup:**
```bash
docker compose build
```

**Start everything:**
```bash
docker compose up
```

Startup order is enforced automatically:
1. Postgres and Redis start and pass healthchecks
2. `migrate` service runs `alembic upgrade head` and exits
3. `gateway` and `worker` start

**Useful commands:**
```bash
docker compose up -d                     # run detached
docker compose logs -f gateway worker    # stream logs
docker compose down                      # stop and remove containers
docker compose down -v                   # also wipe the postgres volume
```

**After code changes:**
```bash
docker compose build gateway worker
docker compose up
```

---

### Option B — Host (uv + Docker infra only)

Run Postgres and Redis in Docker, but run the Python services directly on your machine. Useful for faster iteration (no image rebuild on code changes).

**Step 1 — Start infra:**
```bash
docker compose up db redis -d
```

**Step 2 — Override DB/Redis URLs to use localhost:**

The default `.env` uses Docker service names (`db`, `redis`). For host dev, override just those two:

```bash
export DATABASE_URL=postgresql+psycopg://buma:buma@localhost:5432/buma
export REDIS_URL=redis://localhost:6379/0
```

Or keep a separate `.env.local` and source it before running.

**Step 3 — Install dependencies:**
```bash
uv sync --dev
```

**Step 4 — Apply migrations:**
```bash
uv run alembic upgrade head
```

**Step 5 — Start the gateway** (terminal 1):
```bash
uv run uvicorn buma.gateway.app:app --reload --port 8000
```

**Step 6 — Start the worker** (terminal 2):
```bash
uv run python -m buma.worker.runner
```

The worker connects to Redis, polls `buma:triage:queue`, and processes events through the full triage pipeline (classify → assign → persist → patch GitHub). It shuts down cleanly on `Ctrl+C` or `SIGTERM`.

---

## Gateway API routes

| Method | Route | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/webhook/github` | GitHub webhook receiver |
| `GET` | `/auth/github` | Initiate OAuth login |
| `GET` | `/auth/callback` | OAuth callback |
| `POST` | `/api/config/repos` | Enroll a repository |
| `GET` | `/api/config/repos/{repo_id}` | Get repo config |
| `PATCH` | `/api/config/repos/{repo_id}` | Update repo config |
| `POST` | `/api/config/repos/{repo_id}/developers` | Add a developer profile |
| `PATCH` | `/api/config/repos/{repo_id}/developers/{login}` | Update a developer profile |
| `DELETE` | `/api/config/repos/{repo_id}/developers/{login}` | Remove a developer profile |
| `GET` | `/api/triage/{repo_id}` | Triage decision history (paginated) |
| `GET` | `/api/workload/{repo_id}` | Developer workload view |

All `/api/*` routes require a valid session cookie (GitHub OAuth login).

---

## Scripts

Local development and CI run the same scripts — avoid duplicating logic in workflow YAML.

| Script | What it does |
|---|---|
| `./scripts/lint.sh` | `ruff` lint + `black --check` |
| `./scripts/test.sh` | `pytest` + coverage gate (80% minimum) |
| `./scripts/codegen.sh` | OpenAPI model generation (skips if `openapi.yaml` absent) |
| `uv run python scripts/smoke.py run` | End-to-end local smoke test |

Run these before submitting a PR:
```bash
./scripts/lint.sh
./scripts/test.sh
```

### Smoke test

Requires Option B (host) dev setup — infra running, migrations applied.

```bash
# All phases in one command:
uv run python scripts/smoke.py run

# Or step-by-step:
uv run python scripts/smoke.py seed
uv run python scripts/smoke.py gateway      # separate terminal — Ctrl+C to stop
uv run python scripts/smoke.py webhook
export SMOKE_DELIVERY_ID=<value printed above>
uv run python scripts/smoke.py worker
uv run python scripts/smoke.py verify
uv run python scripts/smoke.py preview

# API endpoints smoke test:
uv run python scripts/smoke.py api
```

> Do not run as `./scripts/smoke.py` — the shebang does not resolve to the uv virtualenv.

---

## Dev container

For a fully managed toolchain (Python, uv, Docker-outside-of-Docker, kubectl, kustomize), open this repo in VS Code and choose **Dev Containers: Reopen in Container**. The `postCreateCommand` runs `uv sync --dev && uv run alembic upgrade head` automatically on first open.

---

## Repository layout

```
src/buma/
├── core/           — settings, security (HMAC)
├── db/             — ORM models, SQLAlchemy base
├── schemas/        — NormalizedEvent (gateway↔worker contract) + API schemas
├── gateway/        — FastAPI ingest service + dashboard API
└── worker/         — async queue consumer + triage pipeline

tests/              — mirrors src/buma/
migrations/         — Alembic migrations
scripts/            — lint, test, codegen, smoke test
.devcontainer/      — VS Code dev container config
.github/            — CI workflow + issue templates
contributors/       — team notes
```

---

## Contributing

### Workflow

1. Create or pick up work via GitHub issues (use the templates).
2. Create a feature branch and open a PR.
3. Keep PRs small and focused — one behavioural change per PR.
4. Run lint and tests locally before requesting review:

```bash
./scripts/lint.sh
./scripts/test.sh
```

### Code style

- Formatter: `black` (line length 120)
- Linter: `ruff` (rules E, F, I, N, W, UP — Python 3.11 target)
- Tests: `pytest` with `asyncio_mode = "auto"`; 80% coverage enforced

### Dependencies

```bash
uv add <package>          # runtime dependency
uv add --dev <package>    # dev-only dependency
```

Commit both `pyproject.toml` and `uv.lock`.

### Scope guardrails

The capstone success criterion is **"works every time"** for the P0 pipeline.

- Prioritise reliability, idempotency, and debuggability over new features.
- Never merge P1/roadmap work if it reduces P0 stability.
- Add one major capability at a time; validate end-to-end before layering more.

### Secrets and security

- Never commit secrets (`.env`, credentials, private keys).
- `.env` is gitignored. Use `.env.example` to document required variables.

### Adding yourself (optional)

Add a short file under `contributors/` (e.g. `contributors/your-name.md`) with your name, role, and GitHub handle.

---

## Resources

- [GitHub Webhooks docs](https://docs.github.com/webhooks)
- [Validating webhook payloads](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)
- [GitHub Apps documentation](https://docs.github.com/apps)

---

## License

A project license has not been added yet. Do not assume reuse permissions until a `LICENSE` file is present.
