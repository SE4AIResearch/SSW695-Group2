"""
Database operations for the smoke test.

Responsibilities:
  - seed_database:        wipe previous smoke data and insert fresh fixtures
  - fetch_triage_results: query the records written by the worker pipeline
  - TriageResults:        typed container for the fetched records

Developer fixtures and their expected assignment outcomes
─────────────────────────────────────────────────────────
  emmanuel  skills=[bug]     capacity=5  open=0  repo=REPO_ID       → SELECTED (right skills, has capacity)
  zeal    skills=[feature] capacity=5  open=0  repo=REPO_ID       → SKIPPED  (wrong skills)
  askay  skills=[bug]     capacity=3  open=3  repo=REPO_ID       → SKIPPED  (at full capacity)
  luis   skills=[bug]     capacity=5  open=0  repo=OTHER_REPO_ID → SKIPPED  (wrong repo)
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from buma.db.models import DeveloperProfile, IssueSnapshot, RepoConfig, TriageDecision, WebhookDelivery
from smoke.config import DEVELOPER_LOGIN, INSTALLATION_ID, OTHER_REPO_ID, REPO_FULL_NAME, REPO_ID
from smoke.console import info, ok


@dataclass
class TriageResults:
    """Holds the DB records written by the worker for a single processed event."""

    snapshot: IssueSnapshot | None
    decision: TriageDecision | None
    developer: DeveloperProfile | None


async def seed_database(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Wipe any previous smoke-test data and insert a fresh set of fixtures
    that exercise all three assignment selection rules:
      - skills matching
      - capacity checking
      - repo isolation
    """
    async with session_factory() as session:
        # Delete in FK-safe order (children before parent)
        await session.execute(delete(TriageDecision).where(TriageDecision.repo_id == REPO_ID))
        await session.execute(delete(IssueSnapshot).where(IssueSnapshot.repo_id == REPO_ID))
        await session.execute(delete(WebhookDelivery).where(WebhookDelivery.repo_id == REPO_ID))
        await session.execute(delete(DeveloperProfile).where(DeveloperProfile.repo_id == REPO_ID))
        await session.execute(delete(RepoConfig).where(RepoConfig.repo_id == REPO_ID))

        # Also clean up luis's other-repo fixture from previous runs
        await session.execute(delete(DeveloperProfile).where(DeveloperProfile.repo_id == OTHER_REPO_ID))
        await session.execute(delete(RepoConfig).where(RepoConfig.repo_id == OTHER_REPO_ID))

        # In production, the dashboard + gateway enrollment routes will eventually provide these.
        session.add(
            RepoConfig(
                repo_id=REPO_ID,
                installation_id=INSTALLATION_ID,
                repo_full_name=REPO_FULL_NAME,
                config={
                    "label_map": {
                        "categories": {"crash": "bug"},
                        "priorities": {"blocker": "P0"},
                    },
                    "defaults": {
                        "category": "bug",
                        "priority": "P2",
                    },
                },
            )
        )
        # A second repo to prove cross-repo isolation (luis belongs here, not to REPO_ID)
        session.add(
            RepoConfig(
                repo_id=OTHER_REPO_ID,
                installation_id=INSTALLATION_ID,
                repo_full_name="smoke-org/other-repo",
                config={},
            )
        )
        # Flush both RepoConfig rows before inserting DeveloperProfiles (FK constraint)
        await session.flush()

        # emmanuel — correct skills, has capacity → WILL be selected
        session.add(
            DeveloperProfile(
                repo_id=REPO_ID,
                github_login="emmanuel",
                skills=["bug"],
                max_capacity=5,
                open_assignments=0,
            )
        )
        # zeal — wrong skills (feature, not bug) → WILL be skipped
        session.add(
            DeveloperProfile(
                repo_id=REPO_ID,
                github_login="zeal",
                skills=["feature"],
                max_capacity=5,
                open_assignments=0,
            )
        )
        # askay — correct skills but at full capacity → WILL be skipped
        session.add(
            DeveloperProfile(
                repo_id=REPO_ID,
                github_login="askay",
                skills=["bug"],
                max_capacity=3,
                open_assignments=3,
            )
        )
        # luis — correct skills and capacity but enrolled in a different repo → WILL be skipped
        session.add(
            DeveloperProfile(
                repo_id=OTHER_REPO_ID,
                github_login="luis",
                skills=["bug"],
                max_capacity=5,
                open_assignments=0,
            )
        )
        await session.commit()

    ok(f"RepoConfig        repo_id={REPO_ID}  full_name={REPO_FULL_NAME}  config=label_map+defaults")
    ok(f"RepoConfig        repo_id={OTHER_REPO_ID}  full_name=smoke-org/other-repo  (isolation fixture)")
    info("Developer profiles seeded:")
    info("  emmanuel  skills=[bug]     capacity=5  open=0  repo=REPO_ID       → expect: SELECTED")
    info("  zeal    skills=[feature] capacity=5  open=0  repo=REPO_ID       → expect: SKIPPED (wrong skills)")
    info("  askay  skills=[bug]     capacity=3  open=3  repo=REPO_ID       → expect: SKIPPED (at capacity)")
    info("  luis   skills=[bug]     capacity=5  open=0  repo=OTHER_REPO_ID → expect: SKIPPED (wrong repo)")


async def fetch_triage_results(
    session_factory: async_sessionmaker[AsyncSession],
    delivery_id: str,
) -> TriageResults:
    """Query the DB for the IssueSnapshot, TriageDecision, and DeveloperProfile written by the pipeline."""
    async with session_factory() as session:
        snapshot = (
            await session.execute(select(IssueSnapshot).where(IssueSnapshot.delivery_id == delivery_id))
        ).scalar_one_or_none()

        decision = (
            await session.execute(select(TriageDecision).where(TriageDecision.delivery_id == delivery_id))
        ).scalar_one_or_none()

        developer = (
            await session.execute(
                select(DeveloperProfile).where(
                    DeveloperProfile.repo_id == REPO_ID,
                    DeveloperProfile.github_login == DEVELOPER_LOGIN,
                )
            )
        ).scalar_one_or_none()

    return TriageResults(snapshot=snapshot, decision=decision, developer=developer)
