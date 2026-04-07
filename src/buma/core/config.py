from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    github_webhook_secret: str

    # GitHub App credentials — required for Phase 6 (GitHub patch).
    # If either is absent, Phase 6 is skipped and patch_state stays DECIDED.
    github_app_id: int | None = None
    github_app_private_key: str | None = None  # PEM content, newlines as \n

    # GitHub OAuth App credentials — required for dashboard login.
    # Register a GitHub OAuth App at github.com/settings/developers.
    github_oauth_client_id: str | None = None
    github_oauth_client_secret: str | None = None

    # Session cookie signing key. Override with a strong random value in production.
    session_secret: str = "dev-secret-change-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
