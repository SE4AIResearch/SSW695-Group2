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

This repository currently contains foundational scaffolding:

- Python package skeleton (`src/buma/`) with a minimal health module
- Unit tests (`tests/`)
- Devcontainer for a consistent toolchain (`.devcontainer/`)
- Script “contracts” for local checks (`scripts/`)
- GitHub issue templates (`.github/ISSUE_TEMPLATE/`)

Core runtime services (ingest API / worker / dashboard / database / queue) are in progress and will be added as the project implementation proceeds.

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



## License

A project license has not been added yet. Do not assume reuse permissions until a `LICENSE` file is present.
