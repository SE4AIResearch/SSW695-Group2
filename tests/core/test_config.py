from __future__ import annotations

import os
from unittest.mock import patch

from buma.core.config import Settings, get_settings


def test_settings_required_fields():
    s = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="my-secret",
    )
    assert s.database_url == "postgresql+psycopg://test:test@localhost/test"
    assert s.github_webhook_secret == "my-secret"


def test_settings_redis_url_default():
    s = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="my-secret",
    )
    assert s.redis_url == "redis://localhost:6379/0"


def test_settings_redis_url_override():
    s = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="my-secret",
        redis_url="redis://myredis:6379/2",
    )
    assert s.redis_url == "redis://myredis:6379/2"


def test_oauth_fields_default_to_none():
    s = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="secret",
    )
    assert s.github_oauth_client_id is None
    assert s.github_oauth_client_secret is None


def test_session_secret_has_dev_default():
    s = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="secret",
    )
    assert s.session_secret == "dev-secret-change-in-production"


def test_session_secret_can_be_overridden():
    s = Settings(
        database_url="postgresql+psycopg://test:test@localhost/test",
        github_webhook_secret="secret",
        session_secret="my-real-secret",
    )
    assert s.session_secret == "my-real-secret"


def test_get_settings_is_cached():
    with patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql+psycopg://test:test@localhost/test", "GITHUB_WEBHOOK_SECRET": "secret"},
    ):
        get_settings.cache_clear()
        try:
            s1 = get_settings()
            s2 = get_settings()
            assert s1 is s2
        finally:
            get_settings.cache_clear()
