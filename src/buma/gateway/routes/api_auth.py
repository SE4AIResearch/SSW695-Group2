"""
Token-based auth endpoints consumed by the React dashboard.

The UI performs GitHub OAuth entirely in the browser:
  1. Login.jsx redirects to github.com/login/oauth/authorize
  2. GitHub redirects back to http://localhost:3000/auth/callback?code=...
  3. AuthCallback.jsx POSTs the code here to exchange it for a JWT
  4. The JWT is stored in localStorage and sent as Authorization: Bearer on every API call

This is separate from the server-side redirect flow in routes/auth.py.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from buma.core.config import Settings, get_settings
from buma.gateway.services.oauth import OAuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class _GitHubCodeRequest(BaseModel):
    code: str


class _LoginRequest(BaseModel):
    email: str
    password: str


def _get_oauth_service(settings: Annotated[Settings, Depends(get_settings)]) -> OAuthService:
    return OAuthService(settings)


@router.post("/github")
async def github_token(
    body: _GitHubCodeRequest,
    svc: Annotated[OAuthService, Depends(_get_oauth_service)],
) -> dict:
    """
    Exchange a GitHub OAuth authorization code for a Buma JWT.

    Called by AuthCallback.jsx after GitHub redirects back to the UI.
    Returns { token, user } — token goes into localStorage, user is displayed in the header.
    """
    try:
        login = await svc.exchange_code(body.code)
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub OAuth exchange failed.")

    token = svc.create_session(login)
    return {
        "token": token,
        "user": {
            "login": login,
            "name": login,
            "github_username": login,
        },
    }


@router.post("/login")
async def email_login(_body: _LoginRequest) -> dict:
    """
    Email/password login stub.

    Not implemented for MVP — the UI has a built-in mock fallback that activates
    when this endpoint returns an error, so local development works without credentials.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email/password login is not supported. Use GitHub OAuth.",
    )
