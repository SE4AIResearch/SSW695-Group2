from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from buma.db.models import RepoConfig


class RepoConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, installation_id: int, repo_full_name: str, config: dict) -> RepoConfig:
        record = RepoConfig(
            installation_id=installation_id,
            repo_full_name=repo_full_name,
            config=config,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_by_id(self, repo_id: int) -> RepoConfig | None:
        result = await self._session.execute(select(RepoConfig).where(RepoConfig.repo_id == repo_id))
        return result.scalar_one_or_none()

    async def list_all(self, limit: int, offset: int) -> tuple[list[RepoConfig], int]:
        total_result = await self._session.execute(select(func.count()).select_from(RepoConfig))
        total = total_result.scalar_one()
        rows_result = await self._session.execute(
            select(RepoConfig).order_by(RepoConfig.repo_id).limit(limit).offset(offset)
        )
        return list(rows_result.scalars().all()), total

    async def update_config(self, repo_id: int, config: dict) -> RepoConfig | None:
        record = await self.get_by_id(repo_id)
        if record is None:
            return None
        record.config = config
        record.updated_at = datetime.now(UTC)
        await self._session.flush()
        return record
