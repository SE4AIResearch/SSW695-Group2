from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from buma.gateway.repositories.developer_profile import DeveloperProfileRepository
from buma.gateway.repositories.repo_config import RepoConfigRepository
from buma.schemas.api.developer_profile import DeveloperProfileCreate, DeveloperProfileResponse, DeveloperProfileUpdate
from buma.schemas.api.repo_config import RepoConfigCreate, RepoConfigListResponse, RepoConfigResponse, RepoConfigUpdate


class RepoNotFoundError(Exception):
    pass


class DeveloperNotFoundError(Exception):
    pass


class DeveloperAlreadyExistsError(Exception):
    pass


class ConfigService:
    def __init__(
        self,
        session: AsyncSession,
        repo_config_repo: RepoConfigRepository,
        developer_profile_repo: DeveloperProfileRepository,
    ) -> None:
        self._session = session
        self._repo_config_repo = repo_config_repo
        self._developer_profile_repo = developer_profile_repo

    # ------------------------------------------------------------------
    # RepoConfig
    # ------------------------------------------------------------------

    async def enroll_repo(self, body: RepoConfigCreate) -> RepoConfigResponse:
        record = await self._repo_config_repo.create(
            installation_id=body.installation_id,
            repo_full_name=body.repo_full_name,
            config=body.config.model_dump(),
        )
        await self._session.commit()
        return RepoConfigResponse.model_validate(record, from_attributes=True)

    async def list_repos(self, limit: int, offset: int) -> RepoConfigListResponse:
        records, total = await self._repo_config_repo.list_all(limit=limit, offset=offset)
        return RepoConfigListResponse(
            repos=[RepoConfigResponse.model_validate(r, from_attributes=True) for r in records],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_repo(self, repo_id: int) -> RepoConfigResponse:
        record = await self._repo_config_repo.get_by_id(repo_id)
        if record is None:
            raise RepoNotFoundError(repo_id)
        return RepoConfigResponse.model_validate(record, from_attributes=True)

    async def update_repo_config(self, repo_id: int, body: RepoConfigUpdate) -> RepoConfigResponse:
        record = await self._repo_config_repo.update_config(repo_id, body.config.model_dump())
        if record is None:
            raise RepoNotFoundError(repo_id)
        await self._session.commit()
        return RepoConfigResponse.model_validate(record, from_attributes=True)

    # ------------------------------------------------------------------
    # DeveloperProfile
    # ------------------------------------------------------------------

    async def add_developer(self, repo_id: int, body: DeveloperProfileCreate) -> DeveloperProfileResponse:
        # Verify repo exists first
        repo = await self._repo_config_repo.get_by_id(repo_id)
        if repo is None:
            raise RepoNotFoundError(repo_id)
        try:
            record = await self._developer_profile_repo.create(
                repo_id=repo_id,
                github_login=body.github_login,
                skills=body.skills,
                max_capacity=body.max_capacity,
            )
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise DeveloperAlreadyExistsError(body.github_login)
        return DeveloperProfileResponse.model_validate(record, from_attributes=True)

    async def update_developer(
        self, repo_id: int, github_login: str, body: DeveloperProfileUpdate
    ) -> DeveloperProfileResponse:
        record = await self._developer_profile_repo.update(
            repo_id=repo_id,
            github_login=github_login,
            skills=body.skills,
            max_capacity=body.max_capacity,
        )
        if record is None:
            raise DeveloperNotFoundError(github_login)
        await self._session.commit()
        return DeveloperProfileResponse.model_validate(record, from_attributes=True)

    async def remove_developer(self, repo_id: int, github_login: str) -> None:
        deleted = await self._developer_profile_repo.delete(repo_id, github_login)
        if not deleted:
            raise DeveloperNotFoundError(github_login)
        await self._session.commit()
