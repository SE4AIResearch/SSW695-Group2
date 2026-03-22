"""
Reporting helpers for the smoke test.

Responsibilities:
  - report_triage_outcome:       validate and print the Phase 5 DB records
  - report_github_patch_preview: show what Phase 6 would have sent to GitHub
"""

from __future__ import annotations

from buma.db.models import TriageDecision
from smoke.config import DEVELOPER_LOGIN, ISSUE_NUMBER, REPO_FULL_NAME
from smoke.console import fail, info, ok, section
from smoke.database import TriageResults


def report_triage_outcome(results: TriageResults) -> None:
    """Print the Phase 5 DB records and exit on any missing record."""
    if not results.snapshot:
        fail("IssueSnapshot NOT found — Phase 5 persistence failed")

    ok(f'IssueSnapshot  issue=#{results.snapshot.issue_number}  title="{results.snapshot.title}"')

    if not results.decision:
        fail("TriageDecision NOT found — Phase 5 persistence failed")

    ok("TriageDecision written:")
    info(f"    category    = {results.decision.predicted_category}")
    info(f"    priority    = {results.decision.predicted_priority}")
    info(f"    confidence  = {results.decision.confidence:.0%}")
    info(f"    assignee    = {results.decision.selected_assignee_login or '(none — no eligible developer)'}")
    info(f"    patch_state = {results.decision.patch_state}")

    if results.developer:
        info(f"    {DEVELOPER_LOGIN}.open_assignments = {results.developer.open_assignments}  (was 0)")

    section(5, "Assignment selection — why each developer was considered")
    info("  emmanuel  skills=[bug]     open=0/5  repo=REPO_ID       → SELECTED  (right skills, has capacity)")
    info("  zeal    skills=[feature] open=0/5  repo=REPO_ID       → SKIPPED   (skills=[feature] ≠ category=bug)")
    info("  askay  skills=[bug]     open=3/3  repo=REPO_ID       → SKIPPED   (open_assignments == max_capacity)")
    info("  luis   skills=[bug]     open=0/5  repo=OTHER_REPO_ID → SKIPPED   (enrolled in a different repo)")


def report_github_patch_preview(decision: TriageDecision) -> None:
    """Show what Phase 6 would have sent to GitHub (preview only — no App credentials)."""
    labels = [decision.predicted_category, decision.predicted_priority]
    assignees = [decision.selected_assignee_login] if decision.selected_assignee_login else []

    info(f"  PATCH /repos/{REPO_FULL_NAME}/issues/{ISSUE_NUMBER}")
    info(f"    labels    = {labels}")
    info(f"    assignees = {assignees}")
    info(f"  POST  /repos/{REPO_FULL_NAME}/issues/{ISSUE_NUMBER}/comments")
    if decision.explanation:
        for line in decision.explanation.splitlines():
            info(f"    {line}")
