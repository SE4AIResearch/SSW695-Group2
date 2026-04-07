from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from buma.db.models import DeveloperProfile, RepoConfig, TriageDecision
from buma.gateway.deps import get_db
from buma.schemas.api.triage import TriageDecisionResponse, TriageHistoryResponse
from buma.schemas.api.workload import DeveloperWorkload, WorkloadResponse

router = APIRouter(prefix="/api", tags=["observability"])


@router.get("/triage/{repo_id}", response_model=TriageHistoryResponse)
async def triage_history(
    repo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TriageHistoryResponse:
    # Verify repo exists
    repo = await db.execute(select(RepoConfig).where(RepoConfig.repo_id == repo_id))
    if repo.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Repo {repo_id} not found.")

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(TriageDecision).where(TriageDecision.repo_id == repo_id)
    )
    total = count_result.scalar_one()

    # Paginated results ordered most-recent first
    rows_result = await db.execute(
        select(TriageDecision)
        .where(TriageDecision.repo_id == repo_id)
        .order_by(TriageDecision.decided_at.desc())
        .limit(limit)
        .offset(offset)
    )
    decisions = [
        TriageDecisionResponse.model_validate(row, from_attributes=True) for row in rows_result.scalars().all()
    ]

    return TriageHistoryResponse(repo_id=repo_id, decisions=decisions, total=total, limit=limit, offset=offset)


@router.get("/workload/{repo_id}", response_model=WorkloadResponse)
async def workload(
    repo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkloadResponse:
    # Verify repo exists
    repo = await db.execute(select(RepoConfig).where(RepoConfig.repo_id == repo_id))
    if repo.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Repo {repo_id} not found.")

    rows_result = await db.execute(
        select(DeveloperProfile)
        .where(DeveloperProfile.repo_id == repo_id)
        .order_by(DeveloperProfile.open_assignments.desc())
    )
    developers = [DeveloperWorkload.model_validate(row, from_attributes=True) for row in rows_result.scalars().all()]

    return WorkloadResponse(repo_id=repo_id, developers=developers)
