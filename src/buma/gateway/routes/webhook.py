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


@router.post(
    "/webhook/github",
    status_code=status.HTTP_202_ACCEPTED,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"type": "object"},
                    "example": {
                        "action": "opened",
                        "installation": {"id": 99001},
                        "repository": {
                            "id": 123456789,
                            "full_name": "smoke-org/smoke-repo",
                            "private": False,
                        },
                        "issue": {
                            "number": 99,
                            "id": 9901,
                            "node_id": "I_swagger_test",
                            "url": "https://api.github.com/repos/smoke-org/smoke-repo/issues/99",
                            "html_url": "https://github.com/smoke-org/smoke-repo/issues/99",
                            "title": "App crashes on login — null pointer exception",
                            "body": "Steps to reproduce: open the app, tap login. Traceback attached.",
                            "labels": [],
                            "user": {"login": "reporter"},
                            "created_at": "2026-04-08T00:00:00Z",
                            "updated_at": "2026-04-08T00:00:00Z",
                        },
                        "sender": {"login": "reporter"},
                    },
                }
            },
        }
    },
)
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: Annotated[str, Header(description="HMAC-SHA256 signature: sha256=<hex>")],
    x_github_event: Annotated[str, Header(description="GitHub event type, e.g. 'issues'")],
    x_github_delivery: Annotated[str, Header(description="GitHub delivery UUID (idempotency key)")],
    settings: Annotated[Settings, Depends(get_settings)] = None,
    service: Annotated[IngestService, Depends(get_ingest_service)] = None,
) -> dict:
    raw_body = await request.body()

    if not verify_github_signature(raw_body, x_hub_signature_256, settings.github_webhook_secret):
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
