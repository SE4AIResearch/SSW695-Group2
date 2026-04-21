from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ProductivityBucket(BaseModel):
    period_start: date
    resolved: int


class DeveloperProductivity(BaseModel):
    github_login: str
    resolved_count: int
    avg_resolution_hours: float | None
    open_assignments: int
    max_capacity: int
    buckets: list[ProductivityBucket]


class ProductivityResponse(BaseModel):
    repo_id: int
    window: str
    developers: list[DeveloperProductivity]
