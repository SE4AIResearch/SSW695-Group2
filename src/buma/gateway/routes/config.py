from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from buma.gateway.deps import get_config_service, require_session
from buma.gateway.services.config import (
    ConfigService,
    DeveloperAlreadyExistsError,
    DeveloperNotFoundError,
    RepoNotFoundError,
)
from buma.schemas.api.developer_profile import DeveloperProfileCreate, DeveloperProfileResponse, DeveloperProfileUpdate
from buma.schemas.api.repo_config import RepoConfigCreate, RepoConfigResponse, RepoConfigUpdate

router = APIRouter(prefix="/api/config", tags=["config"])


@router.post("/repos", response_model=RepoConfigResponse, status_code=status.HTTP_201_CREATED)
async def enroll_repo(
    body: RepoConfigCreate,
    svc: Annotated[ConfigService, Depends(get_config_service)],
    _session: Annotated[str, Depends(require_session)],
) -> RepoConfigResponse:
    return await svc.enroll_repo(body)


@router.get("/repos/{repo_id}", response_model=RepoConfigResponse)
async def get_repo(
    repo_id: int,
    svc: Annotated[ConfigService, Depends(get_config_service)],
    _session: Annotated[str, Depends(require_session)],
) -> RepoConfigResponse:
    try:
        return await svc.get_repo(repo_id)
    except RepoNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Repo {repo_id} not found.")


@router.patch("/repos/{repo_id}", response_model=RepoConfigResponse)
async def update_repo_config(
    repo_id: int,
    body: RepoConfigUpdate,
    svc: Annotated[ConfigService, Depends(get_config_service)],
    _session: Annotated[str, Depends(require_session)],
) -> RepoConfigResponse:
    try:
        return await svc.update_repo_config(repo_id, body)
    except RepoNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Repo {repo_id} not found.")


@router.post(
    "/repos/{repo_id}/developers",
    response_model=DeveloperProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_developer(
    repo_id: int,
    body: DeveloperProfileCreate,
    svc: Annotated[ConfigService, Depends(get_config_service)],
    _session: Annotated[str, Depends(require_session)],
) -> DeveloperProfileResponse:
    try:
        return await svc.add_developer(repo_id, body)
    except RepoNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Repo {repo_id} not found.")
    except DeveloperAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Developer '{e}' already exists in repo.")


@router.patch("/repos/{repo_id}/developers/{github_login}", response_model=DeveloperProfileResponse)
async def update_developer(
    repo_id: int,
    github_login: str,
    body: DeveloperProfileUpdate,
    svc: Annotated[ConfigService, Depends(get_config_service)],
    _session: Annotated[str, Depends(require_session)],
) -> DeveloperProfileResponse:
    try:
        return await svc.update_developer(repo_id, github_login, body)
    except DeveloperNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Developer '{github_login}' not found in repo {repo_id}.",
        )


@router.delete("/repos/{repo_id}/developers/{github_login}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_developer(
    repo_id: int,
    github_login: str,
    svc: Annotated[ConfigService, Depends(get_config_service)],
    _session: Annotated[str, Depends(require_session)],
) -> None:
    try:
        await svc.remove_developer(repo_id, github_login)
    except DeveloperNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Developer '{github_login}' not found in repo {repo_id}.",
        )
