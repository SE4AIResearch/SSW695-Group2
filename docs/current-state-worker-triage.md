# Worker Service — Architecture, Design & Triage Workflow

**Project:** buma — Intelligent Bug Triaging System
**Document scope:** Triage Worker service — internal architecture, processing pipeline, and all phases of `EventProcessorService.process()`
**Last updated:** 2026-03-21
**Implementation status:** Phases 1–5 built and tested. Phase 6 designed, not yet implemented.

---

## 1. Overview

The Triage Worker is a standalone async Python service that consumes `NormalizedEvent` messages from a Redis queue and executes the full triage pipeline: classification, assignee selection, persistence, and GitHub patch. It is the second independently deployable unit in the buma data flow:

```
GitHub Webhook
      │
      ▼
Webhook Ingest Gateway  (FastAPI)
      │  LPUSH
      ▼
Redis  buma:triage:queue
      │  BRPOP
      ▼
Triage Worker  (this service)
      │
      ├──► PostgreSQL  (IssueSnapshot + TriageDecision written)
      └──► GitHub API  (labels, assignee, explanation comment applied)
```

The Worker is intentionally decoupled from the Gateway: it knows nothing about HTTP, webhook signatures, or idempotency at the delivery level. Its responsibility begins when a `NormalizedEvent` is popped from the queue.

**Entry point:** `python -m buma.worker.runner`

---

## 2. Component Architecture

```
buma/worker/
├── runner.py                     ← Process entry point. Wires dependencies, installs signal handlers.
├── consumer.py                   ← QueueConsumer. BRPOP loop. Deserialises messages.
└── services/
    └── event_processor.py        ← EventProcessorService. Full triage pipeline orchestrator.
```

### 2.1 `runner.py` — Process Entry Point

Responsibilities:
- Read settings (`DATABASE_URL`, `REDIS_URL`) from environment via `get_settings()`
- Create the SQLAlchemy `AsyncEngine` and `async_sessionmaker`
- Create the `redis.asyncio` client
- Install `SIGINT` and `SIGTERM` OS signal handlers that set a shared `asyncio.Event`
- Instantiate `EventProcessorService` and `QueueConsumer`
- Call `consumer.run_forever(stop_event=stop_event)` and await until the stop event fires
- In the `finally` block: close the Redis connection and dispose the SQLAlchemy engine

The runner does not contain any business logic. It is purely wiring and lifecycle management.

### 2.2 `QueueConsumer` — Queue Consumer Loop

Responsibilities:
- `run_once()` — pop one message from `buma:triage:queue` using `BRPOP` with a 5-second timeout, deserialise it to a `NormalizedEvent`, delegate to `EventProcessorService.process()`, return `True` (message popped) or `False` (timeout)
- `run_forever(stop_event)` — call `run_once()` in a loop until `stop_event` is set; catch and log unhandled exceptions without stopping the loop

The consumer has no knowledge of triage logic. Its only decision is: *is this a valid `NormalizedEvent`?* If not, it drops the message and logs it. If yes, it delegates entirely to `EventProcessorService`.

**Malformed message handling:** If `BRPOP` returns a payload that fails `NormalizedEvent.model_validate_json()` (either invalid JSON or a schema violation), the consumer logs the first 200 characters and returns `True`. The message is gone from Redis — it cannot be requeued. This is a known trade-off documented in DD-15.

### 2.3 `EventProcessorService` — Triage Pipeline Orchestrator

The single class that owns the full triage pipeline. Each phase is additive — `QueueConsumer` is never modified as phases are added.

`process(event: NormalizedEvent) -> None` is the only public method.

---

## 3. Processing Pipeline — Step by Step

The full pipeline for a single `NormalizedEvent`:

```
QueueConsumer.run_once()
│
│  BRPOP  →  raw bytes
│  model_validate_json()  →  NormalizedEvent
│
▼
EventProcessorService.process(event)
│
│  Step 1: Log receipt
│  Step 2: Load RepoConfig  ──── not enrolled → return (skip)
│  Step 3: Classify category ─── not "bug"   → log + return (skip)
│  Step 4: Classify priority  →  (priority, confidence)
│  Step 5: Select assignee  ────  no eligible dev → assignee=None
│  Step 6: Persist IssueSnapshot + TriageDecision
│  Step 7: Apply GitHub patch (labels / assignee / comment)
│
└── on unhandled exception: write DLQRecord, do not re-raise
```

Each step is described in detail in section 4.

---

## 4. Pipeline Phases

### Phase 1 — Log Receipt ✅ (built)

**Input:** `NormalizedEvent`

Log at INFO level:
```
event_id=<id> repo=<full_name> issue=#<number> action=<action> — received, loading config
```

This log line is the earliest observable trace that a message entered the worker. It fires before any DB or network call.

---

### Phase 2 — Load RepoConfig ✅ (built)

**Input:** `event.repo.id`
**Output:** `RepoConfig | None`

```python
SELECT * FROM repo_config WHERE repo_id = :repo_id
```

**Enrolled:** `RepoConfig` row exists → continue to Phase 3.
**Not enrolled:** `RepoConfig` is `None` → log "not enrolled, skipping" and return. No further processing, no DB writes, no GitHub calls.

This is the primary eligibility gate. A repo must be explicitly enrolled (via the dashboard) before buma processes its issues.

**Why load first:** All subsequent phases — triage rules, assignee pool, label names — depend on per-repo configuration stored in `RepoConfig.config` (JSONB). Loading it first lets every downstream phase use the same config object without additional DB round trips.

---

### Phase 3a — Category Classification ✅ (built)

**Input:** `NormalizedEvent.issue` (title, body, labels), `RepoConfig.config`
**Output:** `category: str`

Classifies the issue into one of the known categories using deterministic rules. No ML is used (P0). Rules are evaluated in this order:

1. **Label-based rules (highest confidence)** — check `event.issue.labels` against the label→category mapping. The mapping has two sources, merged in order:
   - Global defaults (hardcoded in the engine): e.g. `"bug"` → `bug`, `"defect"` → `bug`, `"enhancement"` → `feature`
   - Per-repo overrides in `RepoConfig.config.label_map.categories`: e.g. `"type: defect"` → `bug`
   - Per-repo overrides take precedence over global defaults for the same label.

2. **Keyword rules** — scan `event.issue.title` (and `event.issue.body` if not `None`) for keyword patterns. Bug keywords are split into two tiers with different confidence values (see Phase 3b confidence table). Global keyword lists are defined in the engine. Per-repo keyword overrides can be added via `RepoConfig.config.keyword_overrides`.

3. **Fallback (lowest confidence)** — if no label or keyword rule matches, use `RepoConfig.config.defaults.category` if set, otherwise the engine's global default category.

#### Global label → category mappings

| GitHub label | → Category |
|---|---|
| `bug`, `bug report`, `defect`, `regression` | `bug` |
| `enhancement`, `feature`, `feature request` | `feature` |
| `question`, `help wanted`, `support` | `question` |
| `security`, `vulnerability` | `security` |
| `documentation`, `docs` | `docs` |

#### Global keyword → category mappings

| Keywords | → Category | Confidence |
|---|---|---|
| bug, defect, broken, broke, not working, doesn't work, fails, failing, failure, error, exception, traceback, stack trace, stacktrace, crash, crashes, crashed, panic, regression, incorrect, wrong, unexpected, unable to, cannot, can't, stuck, hang, hung, freeze, frozen, timeout, timed out, blank page, empty page, 500, 502, 503, 504, 404, null pointer, nullpointer, npe, permission denied, auth failed, login fails, cannot login, data loss, corrupt, corrupted, duplicate record, memory leak, deadlock, race condition | `bug` | `0.9` |
| slow, latency, degraded, flaky, intermittent, inconsistent, missing, retry loop, queue stuck, worker stopped, deployment failed, incorrect result, wrong output, not returning, fails on submit, save failed | `bug` | `0.7` |
| add, feature, request, enhancement, support for, ability to, implement | `feature` | `0.7` |
| how to, how do, is it possible, help, can i | `question` | `0.7` |
| security, vulnerability, exploit, injection, auth bypass | `security` | `0.7` |
| documentation, docs, readme, typo, document | `docs` | `0.7` |

#### Category gate — MVP scope enforcement (DD-19)

After classification, if `category != "bug"`:
```
log: event_id=<id> repo=<repo> issue=#<n> category=<category> — not a bug, skipping
return  (no assignment, no persistence, no GitHub patch)
```

This is the designed expansion point. When a new category is ready to be handled, a new branch is added here — the rest of the pipeline is unchanged.

#### Known categories (global defaults)

| Category | Meaning |
|---|---|
| `bug` | Something is broken or behaving incorrectly — **the only category acted on in MVP** |
| `feature` | New functionality requested |
| `question` | User asking for help or clarification |
| `security` | Potential vulnerability or security concern |
| `docs` | Documentation gap or error |

---

### Phase 3b — Priority Classification ✅ (built)

**Input:** `NormalizedEvent.issue` (title, body, labels), `RepoConfig.config`
**Output:** `(priority: str, confidence: float, triage_engine_version: str)`

Only reached if category is `bug`. Classifies the urgency of the bug using the same rules-first approach:

1. **Label-based rules** — check `event.issue.labels` against the label→priority mapping (global defaults + per-repo overrides in `RepoConfig.config.label_map.priorities`).
2. **Keyword rules** — scan title and body for urgency signals. When multiple priority keywords match, the highest priority wins.
3. **Fallback** — `RepoConfig.config.defaults.priority` if set, otherwise the engine's global default priority (`P2`).

#### Global label → priority mappings

| GitHub label | → Priority |
|---|---|
| `P0`, `critical`, `blocker` | `P0` |
| `P1`, `high`, `urgent` | `P1` |
| `P2`, `medium`, `normal` | `P2` |
| `P3`, `low`, `minor`, `trivial` | `P3` |

#### Global keyword → priority mappings

| Keywords | → Priority |
|---|---|
| production down, outage, data loss, data corruption, corrupt, corrupted, deadlock, race condition, memory leak, security breach, all users affected, cannot login, auth failed, permission denied, service unavailable, 500, 502, 503, 504, blank page, empty page, duplicate record, system down, database down, complete failure, critical | `P0` |
| crash, crashes, crashed, panic, exception, traceback, stack trace, stacktrace, null pointer, nullpointer, npe, regression, broken, broke, fails, failing, failure, error, incorrect, wrong output, not working, doesn't work, unable to, cannot, login fails, blank screen, data missing, blocked | `P1` |
| slow, latency, degraded, flaky, intermittent, inconsistent, missing, retry loop, queue stuck, worker stopped, deployment failed, incorrect result, not returning, fails on submit, save failed, timeout, timed out, hang, hung, freeze, frozen, workaround available, affects some users | `P2` |
| cosmetic, minor, typo, nice to have, low priority, trivial, polish, cleanup, formatting, alignment, color, font, spacing, label wrong, text wrong, misleading, confusing, suggestion, improvement | `P3` |

#### Priority levels (global defaults)

| Priority | Meaning |
|---|---|
| `P0` | Production down or data loss — fix immediately |
| `P1` | Significant impact — fix this sprint |
| `P2` | Moderate impact — fix soon |
| `P3` | Low impact or cosmetic — fix when capacity allows |

#### Confidence scoring

| Rule type | Confidence |
|---|---|
| Label match (global default or per-repo override) | `1.0` |
| Keyword match — strong signal | `0.9` |
| Keyword match — medium signal | `0.7` |
| Fallback default | `0.0` |

#### Output fields written to `TriageDecision`

| Field | Type | Value |
|---|---|---|
| `predicted_category` | `str` | `"bug"` (only value acted on in MVP) |
| `predicted_priority` | `str` | `"P0"` – `"P3"` |
| `confidence` | `float` | `0.0` – `1.0` |

---

### Phase 4 — Assignee Selection ✅ (built)

**Input:** `category`, `repo_id`, `AsyncSession`
**Output:** `selected_assignee_login: str | None`

Implemented in `src/buma/worker/services/assignee_selector.py` — `AssigneeSelector.select()`.

Selects the most appropriate developer from the enrolled team for this repo.

#### Session and transaction boundary

`AssigneeSelector.select()` receives an `AsyncSession` from `EventProcessorService` rather than managing its own session. This keeps the `open_assignments` increment and the future `TriageDecision` write (Phase 5) in a **single atomic transaction** — both commit together or neither does. `EventProcessorService` calls `session.commit()` after all Phase 4 and 5 writes complete. (See DD-20.)

#### Selection algorithm

```
1. Query DeveloperProfile
   WHERE repo_id = :repo_id
     AND open_assignments < max_capacity   ← capacity filter
   ORDER BY open_assignments ASC           ← prefer least loaded

2. Filter in Python: keep only candidates where category in candidate.skills

3. For each eligible candidate (in capacity order):
   a. Attempt optimistic lock claim:
      UPDATE developer_profile
         SET open_assignments = open_assignments + 1,
             version = version + 1
       WHERE id = :id
         AND version = :expected_version
   b. await session.flush()
   c. rowcount == 1 → claim succeeded → return candidate.github_login
      rowcount == 0 → concurrent modification → try next candidate

4. No candidate claimed → return None
   (issue is still triaged; no assignee is set in GitHub)
```

**Why optimistic locking:** Multiple Worker instances may process concurrent events for the same repo. A `SELECT` followed by an `UPDATE` without a version check is a read-modify-write race — two workers could both select the same developer and increment their count twice. The `version` column on `DeveloperProfile` prevents this: only one of the two competing updates will see `version = expected_version`; the other will update 0 rows and retry the next candidate. (See GAP-02 in `Architecture-Review-Gaps.md`.)

**No eligible developer:** Not an error. The `TriageDecision` is persisted with `selected_assignee_login = None`. The GitHub patch step will apply labels and the explanation comment but will not set an assignee.

---

### Phase 5 — Persist IssueSnapshot + TriageDecision ✅ (built)

**Input:** `NormalizedEvent`, `category`, `priority`, `confidence`, `selected_assignee_login`
**Output:** `IssueSnapshot` row + `TriageDecision` row written to PostgreSQL

Both writes happen in a **single transaction**. Either both rows are committed or neither is.

#### `IssueSnapshot` — what gets written

| Column | Source |
|---|---|
| `event_id` | `event.event_id` (UNIQUE — idempotency) |
| `delivery_id` | `event.delivery_id` |
| `repo_id` | `event.repo.id` |
| `issue_number` | `event.issue.number` |
| `issue_id` | `event.issue.id` |
| `issue_node_id` | `event.issue.node_id` |
| `title` | `event.issue.title` |
| `body` | `event.issue.body` |
| `labels` | `event.issue.labels` |
| `author_login` | `event.issue.author_login` |
| `issue_created_at` | `event.issue.created_at` |
| `issue_updated_at` | `event.issue.updated_at` |

#### `TriageDecision` — what gets written

| Column | Source |
|---|---|
| `event_id` | `event.event_id` (UNIQUE — idempotency) |
| `delivery_id` | `event.delivery_id` |
| `repo_id` | `event.repo.id` |
| `issue_number` | `event.issue.number` |
| `predicted_category` | triage engine output |
| `predicted_priority` | triage engine output |
| `confidence` | triage engine output |
| `selected_assignee_login` | assignee selection output (may be `None`) |
| `explanation` | generated summary string (see Phase 6) |
| `patch_state` | `"DECIDED"` (initial state) |

#### Explanation string

Generated by `_build_explanation()` in `event_processor.py` and stored in `TriageDecision.explanation`. This string is the single source of truth — Phase 6 uses it verbatim as the GitHub comment body.

```
🤖 **buma triage**
- **Category:** {category}
- **Priority:** {priority}
- **Assigned to:** @{assignee}   ← "*no assignee found*" if None
- **Confidence:** {confidence:.0%}
- **Engine version:** {engine_version}
```

#### Idempotency

Both `IssueSnapshot.event_id` and `TriageDecision.event_id` carry a `UNIQUE` constraint. If a replayed queue message reaches this phase a second time, the INSERT will raise an `IntegrityError`. The worker catches this, treats it as a no-op (the decision already exists), and does not re-apply the GitHub patch. (See GAP-01 in `Architecture-Review-Gaps.md`.)

---

### Phase 6 — GitHub Patch ✅ (built)

**Input:** `NormalizedEvent`, triage result, `assignee_login`, `explanation`
**Output:** Labels applied, assignee set (if any), explanation comment posted on GitHub; `TriageDecision.patch_state` updated

#