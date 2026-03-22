from __future__ import annotations

# ---------------------------------------------------------------------------
# Label → priority (global defaults)
# Per-repo overrides are stored in RepoConfig.config.label_map.priorities
# and merged on top of these at classification time.
# ---------------------------------------------------------------------------
PRIORITY_LABEL_MAP: dict[str, str] = {
    "p0": "P0",
    "critical": "P0",
    "blocker": "P0",
    "p1": "P1",
    "high": "P1",
    "urgent": "P1",
    "p2": "P2",
    "medium": "P2",
    "normal": "P2",
    "p3": "P3",
    "low": "P3",
    "minor": "P3",
    "trivial": "P3",
}

# ---------------------------------------------------------------------------
# Keyword → priority
# All tiers are scanned; highest matching priority wins (P0 > P1 > P2 > P3).
# Phrases are matched (substring) against lowercased title + body.
# ---------------------------------------------------------------------------
PRIORITY_KEYWORDS: dict[str, frozenset[str]] = {
    "P0": frozenset(
        {
            "production down",
            "outage",
            "data loss",
            "data corruption",
            "corrupt",
            "corrupted",
            "deadlock",
            "race condition",
            "memory leak",
            "security breach",
            "all users affected",
            "cannot login",
            "auth failed",
            "permission denied",
            "service unavailable",
            "500",
            "502",
            "503",
            "504",
            "blank page",
            "empty page",
            "duplicate record",
            "system down",
            "database down",
            "complete failure",
            "critical",
        }
    ),
    "P1": frozenset(
        {
            "crash",
            "crashes",
            "crashed",
            "panic",
            "exception",
            "traceback",
            "stack trace",
            "stacktrace",
            "null pointer",
            "nullpointer",
            "npe",
            "regression",
            "broken",
            "broke",
            "fails",
            "failing",
            "failure",
            "error",
            "incorrect",
            "wrong output",
            "not working",
            "doesn't work",
            "unable to",
            "cannot",
            "login fails",
            "blank screen",
            "data missing",
            "blocked",
        }
    ),
    "P2": frozenset(
        {
            "slow",
            "latency",
            "degraded",
            "flaky",
            "intermittent",
            "inconsistent",
            "missing",
            "retry loop",
            "queue stuck",
            "worker stopped",
            "deployment failed",
            "incorrect result",
            "not returning",
            "fails on submit",
            "save failed",
            "timeout",
            "timed out",
            "hang",
            "hung",
            "freeze",
            "frozen",
            "workaround available",
            "affects some users",
        }
    ),
    "P3": frozenset(
        {
            "cosmetic",
            "minor",
            "typo",
            "nice to have",
            "low priority",
            "trivial",
            "polish",
            "cleanup",
            "formatting",
            "alignment",
            "color",
            "font",
            "spacing",
            "label wrong",
            "text wrong",
            "misleading",
            "confusing",
            "suggestion",
            "improvement",
        }
    ),
}

# Defines the evaluation order for highest-priority-wins tie-break.
PRIORITY_ORDER: list[str] = ["P0", "P1", "P2", "P3"]
