from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse

from buma.core.config import Settings, get_settings
from buma.gateway.services.oauth import COOKIE_NAME, SESSION_TTL_HOURS, OAuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_oauth_service(settings: Annotated[Settings, Depends(get_settings)]) -> OAuthService:
    return OAuthService(settings)


@router.get("/github")
async def github_login(
    svc: Annotated[OAuthService, Depends(_get_oauth_service)],
) -> RedirectResponse:
    """Redirect the browser to GitHub's OAuth authorisation page."""
    state = secrets.token_urlsafe(16)
    return RedirectResponse(url=svc.build_redirect_url(state), status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def github_callback(
    code: Annotated[str, Query()],
    response: Response,
    svc: Annotated[OAuthService, Depends(_get_oauth_service)],
) -> dict:
    """Exchange GitHub code for a session cookie."""
    try:
        login = await svc.exchange_code(code)
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub OAuth exchange failed.")

    cookie_value = svc.create_session(login)
    response.set_cookie(
        key=COOKIE_NAME,
        value=cookie_value,
        httponly=True,
        samesite="lax",
        secure=False,  # set True behind HTTPS in production
        max_age=SESSION_TTL_HOURS * 3600,
    )
    return {"login": login}


@router.post("/logout")
async def logout(response: Response) -> dict:
    """Clear the session cookie."""
    response.delete_cookie(COOKIE_NAME)
    return {"status": "logged out"}
