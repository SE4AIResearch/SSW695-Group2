from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Must stay in sync with category_rules.py and priority_rules.py in the worker.
VALID_CATEGORIES: frozenset[str] = frozenset({"bug", "feature", "question", "security", "docs"})
VALID_PRIORITIES: frozenset[str] = frozenset({"P0", "P1", "P2", "P3"})


class LabelMap(BaseModel):
    categories: dict[str, str] = Field(default_factory=dict)
    priorities: dict[str, str] = Field(default_factory=dict)

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: dict[str, str]) -> dict[str, str]:
        invalid = {cat for cat in v.values() if cat not in VALID_CATEGORIES}
        if invalid:
            raise ValueError(f"Invalid category value(s) {invalid}. Must be one of {VALID_CATEGORIES}.")
        return v

    @field_validator("priorities")
    @classmethod
    def validate_priorities(cls, v: dict[str, str]) -> dict[str, str]:
        invalid = {pri for pri in v.values() if pri not in VALID_PRIORITIES}
        if invalid:
            raise ValueError(f"Invalid priority value(s) {invalid}. Must be one of {VALID_PRIORITIES}.")
        return v


class DefaultSettings(BaseModel):
    category: str = "bug"
    priority: str = "P2"

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"Invalid default category '{v}'. Must be one of {VALID_CATEGORIES}.")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in VALID_PRIORITIES:
            raise ValueError(f"Invalid default priority '{v}'. Must be one of {VALID_PRIORITIES}.")
        return v


class RepoConfigSettings(BaseModel):
    label_map: LabelMap = Field(default_factory=LabelMap)
    defaults: DefaultSettings = Field(default_factory=DefaultSettings)


class RepoConfigCreate(BaseModel):
    installation_id: int
    repo_full_name: str
    config: RepoConfigSettings = Field(default_factory=RepoConfigSettings)


class RepoConfigUpdate(BaseModel):
    config: RepoConfigSettings


class RepoConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    repo_id: int
    installation_id: int
    repo_full_name: str
    config: RepoConfigSettings
    created_at: datetime
    updated_at: datetime
