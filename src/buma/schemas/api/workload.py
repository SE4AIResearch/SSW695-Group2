from __future__ import annotations

from pydantic import BaseModel, ConfigDict, computed_field


class DeveloperWorkload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    github_login: str
    skills: list[str]
    max_capacity: int
    open_assignments: int

    @computed_field
    @property
    def available_capacity(self) -> int:
        return max(0, self.max_capacity - self.open_assignments)


class WorkloadResponse(BaseModel):
    repo_id: int
    developers: list[DeveloperWorkload]
