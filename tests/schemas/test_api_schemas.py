from __future__ import annotations

from datetime import UTC, datetime

import pytest
from buma.schemas.api.developer_profile import (
    DeveloperProfileCreate,
    DeveloperProfileResponse,
    DeveloperProfileUpdate,
)
from buma.schemas.api.repo_config import (
    RepoConfigCreate,
    RepoConfigResponse,
    RepoConfigSettings,
)
from buma.schemas.api.triage import TriageDecisionResponse
from buma.schemas.api.workload import DeveloperWorkload, WorkloadResponse
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# RepoConfigSettings
# ---------------------------------------------------------------------------


def test_repo_config_settings_defaults():
    s = RepoConfigSettings()
    assert s.label_map.categories == {}
    assert s.label_map.priorities == {}
    assert s.defaults.category == "bug"
    assert s.defaults.priority == "P2"


def test_repo_config_settings_valid_full():
    s = RepoConfigSettings.model_validate(
        {
            "label_map": {
                "categories": {"crash": "bug", "enhancement": "feature"},
                "priorities": {"blocker": "P0", "high": "P1"},
            },
            "defaults": {"category": "feature", "priority": "P1"},
        }
    )
    assert s.label_map.categories["crash"] == "bug"
    assert s.label_map.priorities["blocker"] == "P0"
    assert s.defaults.priority == "P1"


def test_repo_config_invalid_category_in_label_map():
    with pytest.raises(ValidationError, match="category"):
        RepoConfigSettings.model_validate({"label_map": {"categories": {"crash": "not-a-category"}}})


def test_repo_config_invalid_priority_in_label_map():
    with pytest.raises(ValidationError, match="priority"):
        RepoConfigSettings.model_validate({"label_map": {"priorities": {"blocker": "CRITICAL"}}})


def test_repo_config_invalid_default_category():
    with pytest.raises(ValidationError):
        RepoConfigSettings.model_validate({"defaults": {"category": "unknown"}})


def test_repo_config_invalid_default_priority():
    with pytest.raises(ValidationError):
        RepoConfigSettings.model_validate({"defaults": {"priority": "P9"}})


# ---------------------------------------------------------------------------
# RepoConfigCreate
# ---------------------------------------------------------------------------


def test_repo_config_create_required_fields():
    r = RepoConfigCreate(installation_id=1, repo_full_name="org/repo")
    assert r.installation_id == 1
    assert r.repo_full_name == "org/repo"
    assert r.config.defaults.category == "bug"


def test_repo_config_create_missing_required_raises():
    with pytest.raises(ValidationError):
        RepoConfigCreate(installation_id=1)  # missing repo_full_name


# ---------------------------------------------------------------------------
# RepoConfigResponse — from_attributes
# ---------------------------------------------------------------------------


def test_repo_config_response_from_attributes():
    class FakeORM:
        repo_id = 42
        installation_id = 999
        repo_full_name = "org/repo"
        config = {"label_map": {"categories": {}, "priorities": {}}, "defaults": {"category": "bug", "priority": "P2"}}
        created_at = datetime(2024, 1, 1, tzinfo=UTC)
        updated_at = datetime(2024, 1, 1, tzinfo=UTC)

    r = RepoConfigResponse.model_validate(FakeORM(), from_attributes=True)
    assert r.repo_id == 42
    assert r.repo_full_name == "org/repo"
    assert r.config.defaults.priority == "P2"


def test_repo_config_response_empty_config_from_attributes():
    """Empty JSONB dict ({}) in DB must still produce valid defaults."""

    class FakeORM:
        repo_id = 1
        installation_id = 1
        repo_full_name = "org/repo"
        config = {}
        created_at = datetime(2024, 1, 1, tzinfo=UTC)
        updated_at = datetime(2024, 1, 1, tzinfo=UTC)

    r = RepoConfigResponse.model_validate(FakeORM(), from_attributes=True)
    assert r.config.defaults.category == "bug"


# ---------------------------------------------------------------------------
# DeveloperProfileCreate
# ---------------------------------------------------------------------------


def test_developer_profile_create_defaults():
    d = DeveloperProfileCreate(github_login="alice")
    assert d.skills == []
    assert d.max_capacity == 5


def test_developer_profile_create_valid_skills():
    d = DeveloperProfileCreate(github_login="alice", skills=["bug", "feature"])
    assert "bug" in d.skills


def test_developer_profile_create_invalid_skill():
    with pytest.raises(ValidationError, match="skill"):
        DeveloperProfileCreate(github_login="alice", skills=["backend"])


def test_developer_profile_create_max_capacity_bounds():
    with pytest.raises(ValidationError):
        DeveloperProfileCreate(github_login="alice", max_capacity=0)
    with pytest.raises(ValidationError):
        DeveloperProfileCreate(github_login="alice", max_capacity=101)


# ---------------------------------------------------------------------------
# DeveloperProfileUpdate — partial
# ---------------------------------------------------------------------------


def test_developer_profile_update_all_optional():
    u = DeveloperProfileUpdate()
    assert u.skills is None
    assert u.max_capacity is None


def test_developer_profile_update_invalid_skill():
    with pytest.raises(ValidationError):
        DeveloperProfileUpdate(skills=["devops"])


# ---------------------------------------------------------------------------
# DeveloperProfileResponse — from_attributes
# ---------------------------------------------------------------------------


def test_developer_profile_response_from_attributes():
    class FakeORM:
        id = 7
        repo_id = 42
        github_login = "alice"
        skills = ["bug"]
        max_capacity = 5
        open_assignments = 2
        created_at = datetime(2024, 1, 1, tzinfo=UTC)
        updated_at = datetime(2024, 1, 1, tzinfo=UTC)

    r = DeveloperProfileResponse.model_validate(FakeORM(), from_attributes=True)
    assert r.github_login == "alice"
    assert r.open_assignments == 2
    # version must NOT appear in the response
    assert not hasattr(r, "version")


# ---------------------------------------------------------------------------
# DeveloperWorkload — computed available_capacity
# ---------------------------------------------------------------------------


def test_developer_workload_available_capacity():
    w = DeveloperWorkload(github_login="bob", skills=["bug"], max_capacity=5, open_assignments=3)
    assert w.available_capacity == 2


def test_developer_workload_never_negative():
    w = DeveloperWorkload(github_login="bob", skills=[], max_capacity=3, open_assignments=5)
    assert w.available_capacity == 0


# ---------------------------------------------------------------------------
# WorkloadResponse
# ---------------------------------------------------------------------------


def test_workload_response_structure():
    w = WorkloadResponse(
        repo_id=1,
        developers=[DeveloperWorkload(github_login="alice", skills=["bug"], max_capacity=5, open_assignments=1)],
    )
    assert len(w.developers) == 1
    assert w.developers[0].available_capacity == 4


# ---------------------------------------------------------------------------
# TriageDecisionResponse — from_attributes
# ---------------------------------------------------------------------------


def test_triage_decision_response_from_attributes():
    class FakeORM:
        event_id = "evt-1"
        delivery_id = "del-1"
        repo_id = 42
        issue_number = 5
        decided_at = datetime(2024, 1, 1, tzinfo=UTC)
        predicted_category = "bug"
        predicted_priority = "P1"
        confidence = 0.9
        selected_assignee_login = "alice"
        explanation = "assigned to alice"
        patch_state = "APPLIED"
        created_at = datetime(2024, 1, 1, tzinfo=UTC)
        updated_at = datetime(2024, 1, 1, tzinfo=UTC)

    r = TriageDecisionResponse.model_validate(FakeORM(), from_attributes=True)
    assert r.event_id == "evt-1"
    assert r.patch_state == "APPLIED"
