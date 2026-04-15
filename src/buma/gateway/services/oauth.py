from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import jwt

from buma.core.config import Settings

COOKIE_NAME = "buma_session"
SESSION_TTL_HOURS = 8
_ALGORITHM = "HS256"


class OAuthService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_redirect_url(self, state: str) -> str:
        """Return the GitHub OAuth authorisation URL."""
        return (
            "https://github.com/login/oauth/authorize"
            f"?client_id={self._settings.github_oauth_client_id}"
            f"&state={state}"
            "&scope=read:user"
        )

    async def exchange_code(self, code: str) -> str:
        """Exchange OAuth code → access token → GitHub login. Returns login."""
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": self._settings.github_oauth_client_id,
                    "client_secret": self._settings.github_oauth_client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
                timeout=10,
            )
            token_resp.raise_for_status()
            access_token = token_resp.json()["access_token"]

            user_resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10,
            )
            user_resp.raise_for_status()
            return user_resp.json()["login"]

    def create_session(self, github_login: str) -> str:
        """Encode login into a signed JWT. Returns the cookie value."""
        payload = {
            "sub": github_login,
            "exp": datetime.now(tz=UTC) + timedelta(hours=SESSION_TTL_HOURS),
        }
        return jwt.encode(payload, self._settings.session_secret, algorithm=_ALGORITHM)

    def get_session_user(self, cookie_value: str) -> str | None:
        """Decode and verify JWT. Returns login, or None on any failure."""
        try:
            payload = jwt.decode(cookie_value, self._settings.session_secret, algorithms=[_ALGORITHM])
            return payload["sub"]
        except jwt.PyJWTError:
            return None
