from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from buma.db.models import RepoConfig
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

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def process(self, event: NormalizedEvent) -> None:
        logger.info(
            "event_id=%s repo=%s issue=#%d action=%s — received, loading config",
            event.event_id,
            event.repo.full_name,
            event.issue.number,
            event.action,
        )

        async with self._session_factory() as session:
            repo_config = await self._load_repo_config(session, event.repo.id)

        if repo_config is None:
            logger.info(
                "event_id=%s repo=%s — not enrolled, skipping",
                event.event_id,
                event.repo.full_name,
            )
            return

        logger.info(
            "event_id=%s repo=%s — config loaded, triage pending",
            event.event_id,
            event.repo.full_name,
        )

    async def _load_repo_config(self, session: AsyncSession, repo_id: int) -> RepoConfig | None:
        result = await session.execute(select(RepoConfig).where(RepoConfig.repo_id == repo_id))
        return result.scalar_one_or_none()
