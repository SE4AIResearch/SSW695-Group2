from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from buma.db.models import DeveloperProfile


class DeveloperProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, repo_id: int, github_login: str, skills: list, max_capacity: int) -> DeveloperProfile:
        record = DeveloperProfile(
            repo_id=repo_id,
            github_login=github_login,
            skills=skills,
            max_capacity=max_capacity,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_login(self, repo_id: int, github_login: str) -> DeveloperProfile | None:
        result = await self._session.execute(
            select(DeveloperProfile)
            .where(DeveloperProfile.repo_id == repo_id)
            .where(DeveloperProfile.github_login == github_login)
        )
        return result.scalar_one_or_none()

    async def list_for_repo(self, repo_id: int) -> list[DeveloperProfile]:
        result = await self._session.execute(
            select(DeveloperProfile)
            .where(DeveloperProfile.repo_id == repo_id)
            .order_by(DeveloperProfile.open_assignments.desc())
        )
        return list(result.scalars().all())

    async def update(
        self,
        repo_id: int,
        github_login: str,
        skills: list | None,
        max_capacity: int | None,
    ) -> DeveloperProfile | None:
        record = await self.get_by_login(repo_id, github_login)
        if record is None:
            return None
        if skills is not None:
            record.skills = skills
        if max_capacity is not None:
            record.max_capacity = max_capacity
        record.updated_at = datetime.now(UTC)
        await self._session.flush()
        return record

    async def delete(self, repo_id: int, github_login: str) -> bool:
        record = await self.get_by_login(repo_id, github_login)
        if record is None:
            return False
        await self._session.delete(record)
        await self._session.flush()
        return True
