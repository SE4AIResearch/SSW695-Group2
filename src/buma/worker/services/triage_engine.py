from __future__ import annotations

import logging
from dataclasses import dataclass

from buma.schemas.normalized_event import IssueRef
from buma.worker.services.category_rules import CATEGORY_KEYWORD_MAP, CATEGORY_LABEL_MAP
from buma.worker.services.priority_rules import PRIORITY_KEYWORDS, PRIORITY_LABEL_MAP, PRIORITY_ORDER

logger = logging.getLogger(__name__)

ENGINE_VERSION = "rules-v1"

DEFAULT_CATEGORY = "bug"
DEFAULT_PRIORITY = "P2"


@dataclass(frozen=True)
class TriageResult:
    category: str
    priority: str
    confidence: float
    engine_version: str


class TriageEngine:
    """
    Classifies a GitHub issue into a category and priority using
    deterministic rules (label matching → keyword matching → fallback).

    Pure logic — no I/O, no DB, no async.
    Rules are defined in category_rules.py and priority_rules.py.
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
            best = min(matched, key=lambda p: PRIORITY_ORDER.index(p))
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
