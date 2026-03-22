from __future__ import annotations

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from buma.db.models import DeveloperProfile

logger = logging.getLogger(__name__)


class AssigneeSelector:
    """
    Selects the most appropriate developer for a bug issue using
    skills matching and capacity-based ordering with optimistic locking.

    Receives an AsyncSession from EventProcessorService so that the
    open_assignments increment and the future TriageDecision write
    commit atomically in one transaction. (See DD-20.)
    """

    async def select(self, session: AsyncSession, repo_id: int, category: str) -> str | None:
        """
        Return the github_login of the selected developer, or None if no
        eligible developer could be claimed.
        """
        candidates = await self._query_candidates(session, repo_id)

        for candidate in candidates:
            if category not in (candidate.skills or []):
                continue

            claimed = await self._claim(session, candidate)
            if claimed:
                logger.info(
                    "repo_id=%d category=%s — assigned to %s (open=%d)",
                    repo_id,
                    category,
                    candidate.github_login,
                    candidate.open_assignments + 1,
                )
                return candidate.github_login

            logger.debug(
                "repo_id=%d candidate=%s — version conflict, trying next",
                repo_id,
                candidate.github_login,
            )

        logger.info("repo_id=%d category=%s — no eligible assignee found", repo_id, category)
        return None

    async def _query_candidates(self, session: AsyncSession, repo_id: int) -> list[DeveloperProfile]:
        result = await session.execute(
            select(DeveloperProfile)
            .where(
                DeveloperProfile.repo_id == repo_id,
                DeveloperProfile.open_assignments < DeveloperProfile.max_capacity,
            )
            .order_by(DeveloperProfile.open_assignments.asc())
        )
        return list(result.scalars().all())

    async def _claim(self, session: AsyncSession, candidate: DeveloperProfile) -> bool:
        result = await session.execute(
            update(DeveloperProfile)
            .where(
                DeveloperProfile.id == candidate.id,
                DeveloperProfile.version == candidate.version,
            )
            .values(
                open_assignments=DeveloperProfile.open_assignments + 1,
                version=DeveloperProfile.version + 1,
            )
        )
        await session.flush()
        return result.rowcount == 1
