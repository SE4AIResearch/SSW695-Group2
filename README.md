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

The P0 pipeline (Phases 1–5) is fully implemented and smoke-tested locally:

- Gateway (`src/buma/gateway/`) — webhook ingest, HMAC validation, Redis publish
- Worker (`src/buma/worker/`) — queue consumer, triage engine, assignee selector, DB persistence, GitHub patch
- Database (`src/buma/db/`) — all 6 ORM models, Alembic migration applied
- Unit tests (`tests/`) + end-to-end smoke test (`scripts/smoke.py`)
- Devcontainer for a consistent toolchain (`.devcontainer/`)

Remaining P0 work: Dashboard (configuration, triage history, workload view).

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
