from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Must stay in sync with VALID_CATEGORIES in repo_config.py.
VALID_SKILLS: frozenset[str] = frozenset({"bug", "feature", "question", "security", "docs"})


class DeveloperProfileCreate(BaseModel):
    github_login: str
    skills: list[str] = Field(default_factory=list)
    max_capacity: int = Field(default=5, ge=1, le=100)

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: list[str]) -> list[str]:
        invalid = set(v) - VALID_SKILLS
        if invalid:
            raise ValueError(f"Invalid skill(s) {invalid}. Must be a subset of {VALID_SKILLS}.")
        return v


class DeveloperProfileUpdate(BaseModel):
    skills: list[str] | None = None
    max_capacity: int | None = Field(default=None, ge=1, le=100)

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            invalid = set(v) - VALID_SKILLS
            if invalid:
                raise ValueError(f"Invalid skill(s) {invalid}. Must be a subset of {VALID_SKILLS}.")
        return v


class DeveloperProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repo_id: int
    github_login: str
    skills: list[str]
    max_capacity: int
    open_assignments: int
    created_at: datetime
    updated_at: datetime
