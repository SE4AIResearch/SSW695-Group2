from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from buma.db.models import DeveloperProfile, IssueSnapshot, RepoConfig, TriageDecision
from buma.gateway.deps import get_db, require_session
from buma.schemas.api.issue import IssueListResponse, IssueSnapshotResponse
from buma.schemas.api.productivity import DeveloperProductivity, ProductivityBucket, ProductivityResponse
from buma.schemas.api.triage import TriageDecisionResponse, TriageHistoryResponse
from buma.schemas.api.workload import DeveloperWorkload, WorkloadResponse

# Maps window → (lookback interval, bucket trunc unit, bucket step interval)
# All strings are compile-time constants — safe to embed directly in SQL via f-string.
_WINDOW_SQL: dict[str, tuple[str, str, str]] = {
    "7d": ("7 days", "day", "1 day"),
    "30d": ("30 days", "week", "1 week"),
    "90d": ("90 days", "month", "1 month"),
    "all": ("12 months", "month", "1 month"),
}

router = APIRouter(prefix="/api", tags=["observability"])


@router.get("/triage/{repo_id}", response_model=TriageHistoryResponse)
async def triage_history(
    repo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _session: Annotated[str, Depends(require_session)],
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
    _session: Annotated[str, Depends(require_session)],
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


@router.get("/productivity/{repo_id}", response_model=ProductivityResponse)
async def productivity(
    repo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _session: Annotated[str, Depends(require_session)],
    window: str = Query(default="30d", pattern="^(7d|30d|90d|all)$"),
) -> ProductivityResponse:
    # Verify repo exists
    repo = await db.execute(select(RepoConfig).where(RepoConfig.repo_id == repo_id))
    if repo.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Repo {repo_id} not found.")

    lookback, trunc_unit, step = _WINDOW_SQL[window]

    # Aggregate stats per developer over the selected window
    agg_sql = text(f"""
        SELECT
            dp.github_login,
            dp.open_assignments,
            dp.max_capacity,
            COUNT(td.event_id) FILTER (WHERE td.closed_at IS NOT NULL)        AS resolved_count,
            AVG(
                EXTRACT(EPOCH FROM (td.closed_at - td.decided_at)) / 3600.0
            ) FILTER (WHERE td.closed_at IS NOT NULL)                          AS avg_resolution_hours
        FROM developer_profile dp
        LEFT JOIN triage_decision td
               ON td.repo_id = dp.repo_id
              AND td.selected_assignee_login = dp.github_login
              AND td.closed_at >= NOW() - INTERVAL '{lookback}'
        WHERE dp.repo_id = :repo_id
        GROUP BY dp.github_login, dp.open_assignments, dp.max_capacity
        ORDER BY resolved_count DESC
        """)
    agg_result = await db.execute(agg_sql, {"repo_id": repo_id})
    agg_rows = agg_result.mappings().all()

    # Time-series buckets per developer (all periods filled even if zero)
    bucket_sql = text(f"""
        SELECT
            dp.github_login,
            gs.period_start::date                                              AS period_start,
            COUNT(td.event_id)                                                 AS resolved
        FROM developer_profile dp
        CROSS JOIN LATERAL generate_series(
            date_trunc('{trunc_unit}', NOW() - INTERVAL '{lookback}'),
            date_trunc('{trunc_unit}', NOW()),
            INTERVAL '{step}'
        ) AS gs(period_start)
        LEFT JOIN triage_decision td
               ON td.repo_id = dp.repo_id
              AND td.selected_assignee_login = dp.github_login
              AND td.closed_at IS NOT NULL
              AND date_trunc('{trunc_unit}', td.closed_at) = gs.period_start
        WHERE dp.repo_id = :repo_id
        GROUP BY dp.github_login, gs.period_start
        ORDER BY dp.github_login, gs.period_start
        """)
    bucket_result = await db.execute(bucket_sql, {"repo_id": repo_id})
    bucket_rows = bucket_result.mappings().all()

    # Group buckets by developer
    buckets_by_login: dict[str, list[ProductivityBucket]] = {}
    for row in bucket_rows:
        login = row["github_login"]
        buckets_by_login.setdefault(login, []).append(
            ProductivityBucket(period_start=row["period_start"], resolved=row["resolved"])
        )

    developers = [
        DeveloperProductivity(
            github_login=row["github_login"],
            resolved_count=row["resolved_count"] or 0,
            avg_resolution_hours=row["avg_resolution_hours"],
            open_assignments=row["open_assignments"],
            max_capacity=row["max_capacity"],
            buckets=buckets_by_login.get(row["github_login"], []),
        )
        for row in agg_rows
    ]

    return ProductivityResponse(repo_id=repo_id, window=window, developers=developers)


@router.get("/issues/{repo_id}", response_model=IssueListResponse)
async def get_all_issues(
    repo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _session: Annotated[str, Depends(require_session)],
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> IssueListResponse:
    # Verify repo exists
    repo = await db.execute(select(RepoConfig).where(RepoConfig.repo_id == repo_id))
    if repo.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Repo {repo_id} not found.")

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(IssueSnapshot).where(IssueSnapshot.repo_id == repo_id)
    )
    total = count_result.scalar_one()

    # Paginated results ordered most-recent snapshot first
    rows_result = await db.execute(
        select(IssueSnapshot)
        .where(IssueSnapshot.repo_id == repo_id)
        .order_by(IssueSnapshot.snapshot_at.desc())
        .limit(limit)
        .offset(offset)
    )
    issues = [IssueSnapshotResponse.model_validate(row, from_attributes=True) for row in rows_result.scalars().all()]

    return IssueListResponse(repo_id=repo_id, issues=issues, total=total, limit=limit, offset=offset)
