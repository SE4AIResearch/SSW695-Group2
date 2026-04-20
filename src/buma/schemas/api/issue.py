from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IssueSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    repo_id: int
    issue_number: int
    title: str
    body: str | None
    labels: list[str]
    author_login: str
    issue_created_at: datetime
    issue_updated_at: datetime
    snapshot_at: datetime


class IssueListResponse(BaseModel):
    repo_id: int
    issues: list[IssueSnapshotResponse]
    total: int
    limit: int
    offset: int
