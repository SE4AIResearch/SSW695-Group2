from __future__ import annotations

import logging

from buma.schemas.normalized_event import NormalizedEvent

logger = logging.getLogger(__name__)


class EventProcessorService:
    """
    Orchestrates the full triage pipeline for a single NormalizedEvent.

    Current state: placeholder — logs receipt only.

    Planned steps (built incrementally):
    1. Load RepoConfig from DB
    2. Rule-based triage engine (category + priority)
    3. Assignee selection (skills + capacity + optimistic locking)
    4. Persist IssueSnapshot + TriageDecision
    5. GitHub patch (labels, assignee, explanation comment)
    """

    async def process(self, event: NormalizedEvent) -> None:
        logger.info(
            "event_id=%s repo=%s issue=#%d action=%s — received, triage pending",
            event.event_id,
            event.repo.full_name,
            event.issue.number,
            event.action,
        )
