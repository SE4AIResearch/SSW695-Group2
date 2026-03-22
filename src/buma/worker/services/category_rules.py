from __future__ import annotations

# ---------------------------------------------------------------------------
# Label → category (global defaults)
# Per-repo overrides are stored in RepoConfig.config.label_map.categories
# and merged on top of these at classification time.
# ---------------------------------------------------------------------------
CATEGORY_LABEL_MAP: dict[str, str] = {
    "bug": "bug",
    "bug report": "bug",
    "defect": "bug",
    "regression": "bug",
    "enhancement": "feature",
    "feature": "feature",
    "feature request": "feature",
    "question": "question",
    "help wanted": "question",
    "support": "question",
    "security": "security",
    "vulnerability": "security",
    "documentation": "docs",
    "docs": "docs",
}

# ---------------------------------------------------------------------------
# Keyword → category
# Phrases are matched (substring) against lowercased title + body.
# ---------------------------------------------------------------------------

# Confidence 0.9 — clear indicators of a broken/failing system
BUG_STRONG_PHRASES: frozenset[str] = frozenset(
    {
        "bug",
        "defect",
        "broken",
        "broke",
        "not working",
        "doesn't work",
        "fails",
        "failing",
        "failure",
        "error",
        "exception",
        "traceback",
        "stack trace",
        "stacktrace",
        "crash",
        "crashes",
        "crashed",
        "panic",
        "regression",
        "incorrect",
        "wrong",
        "unexpected",
        "unable to",
        "cannot",
        "can't",
        "stuck",
        "hang",
        "hung",
        "freeze",
        "frozen",
        "timeout",
        "timed out",
        "blank page",
        "empty page",
        "500",
        "502",
        "503",
        "504",
        "404",
        "null pointer",
        "nullpointer",
        "npe",
        "permission denied",
        "auth failed",
        "login fails",
        "cannot login",
        "data loss",
        "corrupt",
        "corrupted",
        "duplicate record",
        "memory leak",
        "deadlock",
        "race condition",
    }
)

# Confidence 0.7 — degraded or inconsistent behaviour, not an outright failure
BUG_MEDIUM_PHRASES: frozenset[str] = frozenset(
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
        "wrong output",
        "not returning",
        "fails on submit",
        "save failed",
    }
)

# ---------------------------------------------------------------------------
# Ordered keyword map evaluated by _classify_category.
# Each entry: (phrases, category, confidence)
# First match wins — strong bug signals are evaluated before medium ones.
# ---------------------------------------------------------------------------
CATEGORY_KEYWORD_MAP: list[tuple[frozenset[str], str, float]] = [
    (BUG_STRONG_PHRASES, "bug", 0.9),
    (BUG_MEDIUM_PHRASES, "bug", 0.7),
    (
        frozenset({"add", "feature", "request", "enhancement", "support for", "ability to", "implement"}),
        "feature",
        0.7,
    ),
    (
        frozenset({"how to", "how do", "is it possible", "help", "can i"}),
        "question",
        0.7,
    ),
    (
        frozenset({"security", "vulnerability", "exploit", "injection", "auth bypass"}),
        "security",
        0.7,
    ),
    (
        frozenset({"documentation", "docs", "readme", "typo", "document"}),
        "docs",
        0.7,
    ),
]
