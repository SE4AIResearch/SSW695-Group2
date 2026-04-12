from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from buma.core.config import Settings, get_settings

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post(
    "/sign-webhook",
    summary="Sign a webhook payload (dev only)",
    description=(
        "Accepts any JSON payload and returns the compact body plus the three headers "
        "required to call POST /webhook/github. Only available when DEBUG=true. "
        "Never expose this endpoint in production."
    ),
)
async def sign_webhook(
    payload: dict,
    settings: Annotated[Settings, Depends(get_settings)],
    event: str = "issues",
) -> dict:
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    compact_body = json.dumps(payload, separators=(",", ":"))
    sig = (
        "sha256="
        + hmac.new(
            settings.github_webhook_secret.encode(),
            compact_body.encode(),
            hashlib.sha256,
        ).hexdigest()
    )

    return {
        "x_github_event": event,
        "x_github_delivery": str(uuid.uuid4()),
        "x_hub_signature_256": sig,
        "compact_body": compact_body,
    }
