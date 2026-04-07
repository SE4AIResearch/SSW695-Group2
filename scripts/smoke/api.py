"""
API endpoint smoke test — exercises all config and observability routes.

Note: auth (Phase 5) is not yet implemented, so these endpoints are
currently unprotected. A future smoke step will add session headers
once OAuth is in place.
"""

from __future__ import annotations

import httpx

from smoke.config import GATEWAY_URL
from smoke.console import fail, info, ok

# Smoke test fixture values — distinct from the main pipeline fixtures
# so the two smoke tests do not interfere with each other.
API_SMOKE_REPO_FULL_NAME = "api-smoke/test-repo"
API_SMOKE_INSTALLATION_ID = 77001
API_SMOKE_DEVELOPER = "carlos"


def _assert(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        ok(label)
    else:
        fail(f"{label}  {detail}")


def run_api_smoke(base_url: str = GATEWAY_URL) -> None:
    """
    Execute the full API smoke sequence against a running gateway.
    Raises SystemExit(1) on the first failure via fail().
    """
    client = httpx.Client(base_url=base_url, timeout=10.0)

    # ------------------------------------------------------------------
    # 1. Enroll a repo
    # ------------------------------------------------------------------
    info("POST /api/config/repos  →  enroll api-smoke/test-repo")
    r = client.post(
        "/api/config/repos",
        json={
            "installation_id": API_SMOKE_INSTALLATION_ID,
            "repo_full_name": API_SMOKE_REPO_FULL_NAME,
        },
    )
    _assert(r.status_code == 201, "POST /api/config/repos → 201 Created", str(r.text))
    repo_id: int = r.json()["repo_id"]
    _assert(r.json()["repo_full_name"] == API_SMOKE_REPO_FULL_NAME, f"  repo_full_name = {API_SMOKE_REPO_FULL_NAME}")
    _assert(
        r.json()["config"]["defaults"]["category"] == "bug",
        "  config.defaults.category = bug  (default)",
    )
    info(f"  repo_id = {repo_id}  (will be used for all subsequent calls)")

    # ------------------------------------------------------------------
    # 2. Read the repo config back
    # ------------------------------------------------------------------
    info(f"GET /api/config/repos/{repo_id}")
    r = client.get(f"/api/config/repos/{repo_id}")
    _assert(r.status_code == 200, f"GET /api/config/repos/{repo_id} → 200 OK", str(r.text))
    _assert(r.json()["repo_id"] == repo_id, f"  repo_id matches ({repo_id})")

    # ------------------------------------------------------------------
    # 3. Update the repo config (add a custom label mapping)
    # ------------------------------------------------------------------
    info(f"PATCH /api/config/repos/{repo_id}  →  add label_map entry")
    r = client.patch(
        f"/api/config/repos/{repo_id}",
        json={
            "config": {
                "label_map": {
                    "categories": {"crash": "bug", "defect": "bug"},
                    "priorities": {"blocker": "P0"},
                },
                "defaults": {"category": "bug", "priority": "P1"},
            }
        },
    )
    _assert(r.status_code == 200, f"PATCH /api/config/repos/{repo_id} → 200 OK", str(r.text))
    _assert(
        r.json()["config"]["label_map"]["categories"].get("crash") == "bug",
        "  label_map.categories.crash = bug",
    )
    _assert(r.json()["config"]["defaults"]["priority"] == "P1", "  defaults.priority = P1")

    # ------------------------------------------------------------------
    # 4. Add a developer
    # ------------------------------------------------------------------
    info(f"POST /api/config/repos/{repo_id}/developers  →  add {API_SMOKE_DEVELOPER}")
    r = client.post(
        f"/api/config/repos/{repo_id}/developers",
        json={"github_login": API_SMOKE_DEVELOPER, "skills": ["bug", "feature"], "max_capacity": 8},
    )
    _assert(
        r.status_code == 201,
        f"POST /api/config/repos/{repo_id}/developers → 201 Created",
        str(r.text),
    )
    _assert(r.json()["github_login"] == API_SMOKE_DEVELOPER, f"  github_login = {API_SMOKE_DEVELOPER}")
    _assert(r.json()["max_capacity"] == 8, "  max_capacity = 8")
    _assert(r.json()["open_assignments"] == 0, "  open_assignments = 0  (starts at zero)")

    # ------------------------------------------------------------------
    # 5. Duplicate developer → 409 Conflict
    # ------------------------------------------------------------------
    info(f"POST /api/config/repos/{repo_id}/developers  →  duplicate {API_SMOKE_DEVELOPER} → expect 409")
    r = client.post(
        f"/api/config/repos/{repo_id}/developers",
        json={"github_login": API_SMOKE_DEVELOPER},
    )
    _assert(r.status_code == 409, "POST duplicate developer → 409 Conflict", str(r.text))

    # ------------------------------------------------------------------
    # 6. Update developer skills
    # ------------------------------------------------------------------
    info(f"PATCH /api/config/repos/{repo_id}/developers/{API_SMOKE_DEVELOPER}")
    r = client.patch(
        f"/api/config/repos/{repo_id}/developers/{API_SMOKE_DEVELOPER}",
        json={"skills": ["bug", "feature", "security"], "max_capacity": 10},
    )
    _assert(
        r.status_code == 200,
        f"PATCH /api/config/repos/{repo_id}/developers/{API_SMOKE_DEVELOPER} → 200 OK",
        str(r.text),
    )
    _assert("security" in r.json()["skills"], "  skills includes 'security'")
    _assert(r.json()["max_capacity"] == 10, "  max_capacity updated to 10")

    # ------------------------------------------------------------------
    # 7. Workload view — developer present
    # ------------------------------------------------------------------
    info(f"GET /api/workload/{repo_id}")
    r = client.get(f"/api/workload/{repo_id}")
    _assert(r.status_code == 200, f"GET /api/workload/{repo_id} → 200 OK", str(r.text))
    devs = r.json()["developers"]
    _assert(len(devs) == 1, "  workload contains 1 developer")
    _assert(devs[0]["github_login"] == API_SMOKE_DEVELOPER, f"  developer = {API_SMOKE_DEVELOPER}")
    _assert(devs[0]["available_capacity"] == 10, "  available_capacity = 10 (max - open)")

    # ------------------------------------------------------------------
    # 8. Triage history — empty for a fresh repo
    # ------------------------------------------------------------------
    info(f"GET /api/triage/{repo_id}")
    r = client.get(f"/api/triage/{repo_id}")
    _assert(r.status_code == 200, f"GET /api/triage/{repo_id} → 200 OK", str(r.text))
    _assert(r.json()["total"] == 0, "  total = 0  (no issues triaged for this repo yet)")
    _assert(r.json()["limit"] == 100, "  limit = 100  (default)")
    _assert(r.json()["offset"] == 0, "  offset = 0  (default)")

    # ------------------------------------------------------------------
    # 9. Pagination params are respected
    # ------------------------------------------------------------------
    info(f"GET /api/triage/{repo_id}?limit=10&offset=5")
    r = client.get(f"/api/triage/{repo_id}?limit=10&offset=5")
    _assert(r.status_code == 200, "  pagination params accepted → 200 OK", str(r.text))
    _assert(r.json()["limit"] == 10, "  limit = 10")
    _assert(r.json()["offset"] == 5, "  offset = 5")

    # ------------------------------------------------------------------
    # 10. Remove the developer
    # ------------------------------------------------------------------
    info(f"DELETE /api/config/repos/{repo_id}/developers/{API_SMOKE_DEVELOPER}")
    r = client.delete(f"/api/config/repos/{repo_id}/developers/{API_SMOKE_DEVELOPER}")
    _assert(
        r.status_code == 204,
        f"DELETE /api/config/repos/{repo_id}/developers/{API_SMOKE_DEVELOPER} → 204 No Content",
        str(r.text),
    )

    # ------------------------------------------------------------------
    # 11. Workload is empty after removal
    # ------------------------------------------------------------------
    r = client.get(f"/api/workload/{repo_id}")
    _assert(r.json()["developers"] == [], "  workload empty after developer removal")

    # ------------------------------------------------------------------
    # 12. Error cases
    # ------------------------------------------------------------------
    info("Error cases")

    # Use repo_id + 1_000_000 as a guaranteed non-existent ID.
    # This avoids collisions with seed fixtures (REPO_ID=123456789, OTHER_REPO_ID=999999999).
    nonexistent_id = repo_id + 1_000_000

    r = client.get(f"/api/config/repos/{nonexistent_id}")
    _assert(r.status_code == 404, f"GET /api/config/repos/{nonexistent_id} (non-existent) → 404 Not Found")

    r = client.post(
        f"/api/config/repos/{repo_id}/developers",
        json={"github_login": "testdev", "skills": ["devops"]},  # invalid skill
    )
    _assert(r.status_code == 422, "POST developer with invalid skill → 422 Unprocessable Entity")

    r = client.patch(
        f"/api/config/repos/{repo_id}",
        json={"config": {"defaults": {"category": "not-a-category", "priority": "P2"}}},
    )
    _assert(r.status_code == 422, "PATCH repo with invalid category → 422 Unprocessable Entity")

    r = client.get(f"/api/triage/{nonexistent_id}")
    _assert(r.status_code == 404, f"GET /api/triage/{nonexistent_id} (non-existent) → 404 Not Found")

    r = client.get(f"/api/workload/{nonexistent_id}")
    _assert(r.status_code == 404, f"GET /api/workload/{nonexistent_id} (non-existent) → 404 Not Found")

    info(f"Note: repo_id={repo_id} (api-smoke/test-repo) remains in the DB — safe to ignore")
