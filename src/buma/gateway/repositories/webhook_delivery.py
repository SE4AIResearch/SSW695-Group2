from __future__ import annotations

from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from buma.db.models import WebhookDelivery


class WebhookDeliveryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_if_new(
        self,
        *,
        delivery_id: str,
        event_name: str,
        action: str | None,
        installation_id: int,
        repo_id: int,
        repo_full_name: str,
        received_at: datetime,
    ) -> bool:
        """Insert a delivery row. Returns True if inserted, False if delivery_id already exists."""
        self._session.add(
            WebhookDelivery(
                delivery_id=delivery_id,
                event_name=event_name,
                action=action,
                installation_id=installation_id,
                repo_id=repo_id,
                repo_full_name=repo_full_name,
                received_at=received_at,
            )
        )
        try:
            await self._session.flush()
            return True
        except IntegrityError:
            await self._session.rollback()
            return False
