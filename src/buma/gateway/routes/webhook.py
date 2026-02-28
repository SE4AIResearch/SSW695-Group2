from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from buma.core.config import Settings, get_settings
from buma.core.security import verify_github_signature
from buma.gateway.deps import get_ingest_service
from buma.gateway.services.ingest import IngestResult, IngestService

router = APIRouter()


@router.post("/webhook/github", status_code=status.HTTP_202_ACCEPTED)
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
    x_github_event: Annotated[str | None, Header()] = None,
    x_github_delivery: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,
    service: Annotated[IngestService, Depends(get_ingest_service)] = None,
) -> dict:
    if not x_github_event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-GitHub-Event header")
    if not x_github_delivery:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-GitHub-Delivery header")

    raw_body = await request.body()

    if not verify_github_signature(raw_body, x_hub_signature_256 or "", settings.github_webhook_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    try:
        payload = json.loads(raw_body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body") from exc

    result = await service.handle(
        delivery_id=x_github_delivery,
        event_name=x_github_event,
        payload=payload,
        received_at=datetime.now(tz=UTC),
    )

    if result == IngestResult.DUPLICATE:
        return {"status": "duplicate", "delivery_id": x_github_delivery}
    if result == IngestResult.IGNORED:
        return {"status": "ignored", "event": x_github_event}
    return {"status": "queued", "delivery_id": x_github_delivery}
