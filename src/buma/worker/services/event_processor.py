from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from buma.db.models import RepoConfig
from buma.schemas.normalized_event import NormalizedEvent
from buma.worker.services.assignee_selector import AssigneeSelector
from buma.worker.services.triage_engine import TriageEngine

logger = logging.getLogger(__name__)


class EventProcessorService:
    """
    Orchestrates the full triage pipeline for a single NormalizedEvent.

    Phases:
    1. Log receipt
    2. Load RepoConfig from DB — skip if repo not enrolled
    3. Classify category + priority (TriageEngine) — skip if not a bug
    4. Assignee selection (skills + capacity + optimistic locking)
    5. Persist IssueSnapshot + TriageDecision                       [TODO]
    6. GitHub patch (labels, assignee, explanation comment)         [TODO]
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        triage_engine: TriageEngine | None = None,
        assignee_selector: AssigneeSelector | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._engine = triage_engine or TriageEngine()
        self._selector = assignee_selector or AssigneeSelector()

    async def process(self, event: NormalizedEvent) -> None:
        # Phase 1 — log receipt
        logger.info(
            "event_id=%s repo=%s issue=#%d action=%s — received, loading config",
            event.event_id,
            event.repo.full_name,
            event.issue.number,
            event.action,
        )

        # Phase 2 — load RepoConfig
        async with self._session_factory() as session:
            repo_config = await self._load_repo_config(session, event.repo.id)

        if repo_config is None:
            logger.info(
                "event_id=%s repo=%s — not enrolled, skipping",
                event.event_id,
                event.repo.full_name,
            )
            return

        # Phase 3 — classify
        result = self._engine.classify(event.issue, repo_config.config)

        if result.category != "bug":
            logger.info(
                "event_id=%s repo=%s issue=#%d — category=%s, not a bug, skipping",
                event.event_id,
                event.repo.full_name,
                event.issue.number,
                result.category,
            )
            return

        logger.info(
            "event_id=%s repo=%s issue=#%d — category=%s priority=%s confidence=%.2f engine=%s",
            event.event_id,
            event.repo.full_name,
            event.issue.number,
            result.category,
            result.priority,
            result.confidence,
            result.engine_version,
        )

        # Phase 4 — assignee selection
        # Phase 5 — persist IssueSnapshot + TriageDecision [TODO]
        # Both phases share one session so their writes commit atomically (DD-20).
        async with self._session_factory() as session:
            assignee_login = await self._selector.select(session, event.repo.id, result.category)
            # Phase 5 writes will be added here before commit
            await session.commit()

        logger.info(
            "event_id=%s repo=%s issue=#%d — assignee=%s",
            event.event_id,
            event.repo.full_name,
            event.issue.number,
            assignee_login or "none",
        )

        # Phase 6 — GitHub patch [TODO]

    async def _load_repo_config(self, session: AsyncSession, repo_id: int) -> RepoConfig | None:
        result = await session.execute(select(RepoConfig).where(RepoConfig.repo_id == repo_id))
        return result.scalar_one_or_none()
