from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TriageDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    delivery_id: str
    repo_id: int
    issue_number: int
    decided_at: datetime
    predicted_category: str | None
    predicted_priority: str | None
    confidence: float | None
    selected_assignee_login: str | None
    explanation: str | None
    patch_state: str
    created_at: datetime
    updated_at: datetime


class TriageHistoryResponse(BaseModel):
    repo_id: int
    decisions: list[TriageDecisionResponse]
    total: int
    limit: int
    offset: int
