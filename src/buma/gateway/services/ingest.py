from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from buma.gateway.publishers.queue import QueuePublisher
from buma.gateway.repositories.webhook_delivery import WebhookDeliveryRepository
from buma.schemas.normalized_event import SCHEMA_VERSION, IssueRef, NormalizedEvent, RepoRef


class IngestResult(StrEnum):
    QUEUED = "QUEUED"
    DUPLICATE = "DUPLICATE"
    IGNORED = "IGNORED"


class IngestService:
    def __init__(
        self,
        session: AsyncSession,
        repo: WebhookDeliveryRepository,
        publisher: QueuePublisher,
    ) -> None:
        self._session = session
        self._repo = repo
        self._publisher = publisher

    async def handle(
        self,
        *,
        delivery_id: str,
        event_name: str,
        payload: dict,
        received_at: datetime,
    ) -> IngestResult:
        action: str | None = payload.get("action")

        if event_name != "issues" or action != "opened":
            return IngestResult.IGNORED

        installation_id: int = payload["installation"]["id"]
        repo: dict = payload["repository"]
        issue: dict = payload["issue"]

        is_new = await self._repo.insert_if_new(
            delivery_id=delivery_id,
            event_name=event_name,
            action=action,
            installation_id=installation_id,
            repo_id=repo["id"],
            repo_full_name=repo["full_name"],
            received_at=received_at,
        )
        if not is_new:
            return IngestResult.DUPLICATE

        event = NormalizedEvent(
            schema_version=SCHEMA_VERSION,
            event_id=delivery_id,
            delivery_id=delivery_id,
            event_name=event_name,
            action=action,
            received_at=received_at,
            installation_id=installation_id,
            repo=RepoRef(
                id=repo["id"],
                full_name=repo["full_name"],
                private=repo["private"],
            ),
            issue=IssueRef(
                number=issue["number"],
                id=issue["id"],
                node_id=issue["node_id"],
                url=issue["url"],
                html_url=issue["html_url"],
                title=issue["title"],
                body=issue.get("body"),
                labels=[lbl["name"] for lbl in issue.get("labels", [])],
                author_login=issue["user"]["login"],
                created_at=issue["created_at"],
                updated_at=issue["updated_at"],
            ),
            sender_login=payload.get("sender", {}).get("login"),
        )

        await self._publisher.publish(event)
        await self._session.commit()

        return IngestResult.QUEUED
