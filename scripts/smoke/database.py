"""
Database operations for the smoke test.

Responsibilities:
  - seed_database:       wipe previous smoke data and insert fresh fixtures
  - fetch_triage_results: query the records written by the worker pipeline
  - TriageResults:        typed container for the fetched records
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from buma.db.models import DeveloperProfile, IssueSnapshot, RepoConfig, TriageDecision, WebhookDelivery
from smoke.config import DEVELOPER_LOGIN, INSTALLATION_ID, REPO_FULL_NAME, REPO_ID
from smoke.console import ok


@dataclass
class TriageResults:
    """Holds the DB records written by the worker for a single processed event."""

    snapshot: IssueSnapshot | None
    decision: TriageDecision | None
    developer: DeveloperProfile | None


async def seed_database(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Wipe any previous smoke-test data for REPO_ID and insert a fresh
    RepoConfig + DeveloperProfile so the test is fully idempotent.
    """
    async with session_factory() as session:
        # Delete in FK-safe order (children before parent)
        await session.execute(delete(TriageDecision).where(TriageDecision.repo_id == REPO_ID))
        await session.execute(delete(IssueSnapshot).where(IssueSnapshot.repo_id == REPO_ID))
        await session.execute(delete(WebhookDelivery).where(WebhookDelivery.repo_id == REPO_ID))
        await session.execute(delete(DeveloperProfile).where(DeveloperProfile.repo_id == REPO_ID))
        await session.execute(delete(RepoConfig).where(RepoConfig.repo_id == REPO_ID))

        # In production, the dashboard + gateway enrollment routes will eventually provide.
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
        # Flush RepoConfig before DeveloperProfile to satisfy the FK constraint
        await session.flush()

        session.add(
            DeveloperProfile(
                repo_id=REPO_ID,
                github_login=DEVELOPER_LOGIN,
                skills=["bug"],
                max_capacity=5,
                open_assignments=0,
            )
        )
        await session.commit()

    ok(f"RepoConfig        repo_id={REPO_ID}  full_name={REPO_FULL_NAME}  config=label_map+defaults")
    ok(f"DeveloperProfile  login={DEVELOPER_LOGIN}  skills=[bug]  capacity=5")


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
