from __future__ import annotations

import logging
from dataclasses import dataclass

from buma.schemas.normalized_event import IssueRef

logger = logging.getLogger(__name__)

ENGINE_VERSION = "rules-v1"

DEFAULT_CATEGORY = "bug"
DEFAULT_PRIORITY = "P2"

# ---------------------------------------------------------------------------
# Label → category (global defaults)
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
# Label → priority (global defaults)
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
# Keyword → category
# Each entry: (phrases, category, confidence)
# Evaluated in order — first match wins.
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Keyword → priority
# All tiers are scanned; highest matching priority wins.
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

_PRIORITY_ORDER = ["P0", "P1", "P2", "P3"]


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TriageResult:
    category: str
    priority: str
    confidence: float
    engine_version: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class TriageEngine:
    """
    Classifies a GitHub issue into a category and priority using
    deterministic rules (label matching → keyword matching → fallback).

    Pure logic — no I/O, no DB, no async.
    """

    def classify(self, issue: IssueRef, config: dict) -> TriageResult:
        text = self._build_text(issue.title, issue.body)
        category, cat_confidence = self._classify_category(issue.labels, text, config)
        priority, pri_confidence = self._classify_priority(issue.labels, text, config)
        non_zero = [c for c in (cat_confidence, pri_confidence) if c > 0]
        confidence = min(non_zero) if non_zero else 0.0

        logger.debug(
            "category=%s(%.2f) priority=%s(%.2f) overall=%.2f",
            category,
            cat_confidence,
            priority,
            pri_confidence,
            confidence,
        )

        return TriageResult(
            category=category,
            priority=priority,
            confidence=confidence,
            engine_version=ENGINE_VERSION,
        )

    def _classify_category(self, labels: list[str], text: str, config: dict) -> tuple[str, float]:
        label_map = self._merge_maps(CATEGORY_LABEL_MAP, config.get("label_map", {}).get("categories", {}))

        for label in labels:
            category = label_map.get(label.lower())
            if category:
                return category, 1.0

        for phrases, category, confidence in CATEGORY_KEYWORD_MAP:
            if any(phrase in text for phrase in phrases):
                return category, confidence

        default = config.get("defaults", {}).get("category", DEFAULT_CATEGORY)
        return default, 0.0

    def _classify_priority(self, labels: list[str], text: str, config: dict) -> tuple[str, float]:
        label_map = self._merge_maps(PRIORITY_LABEL_MAP, config.get("label_map", {}).get("priorities", {}))

        for label in labels:
            priority = label_map.get(label.lower())
            if priority:
                return priority, 1.0

        matched: list[str] = []
        for priority, phrases in PRIORITY_KEYWORDS.items():
            if any(phrase in text for phrase in phrases):
                matched.append(priority)

        if matched:
            best = min(matched, key=lambda p: _PRIORITY_ORDER.index(p))
            confidence = 0.9 if best in ("P0", "P1") else 0.7
            return best, confidence

        default = config.get("defaults", {}).get("priority", DEFAULT_PRIORITY)
        return default, 0.0

    @staticmethod
    def _build_text(title: str, body: str | None) -> str:
        return (title + " " + (body or "")).lower()

    @staticmethod
    def _merge_maps(global_map: dict[str, str], overrides: dict[str, str]) -> dict[str, str]:
        merged = dict(global_map)
        merged.update({k.lower(): v for k, v in overrides.items()})
        return merged
