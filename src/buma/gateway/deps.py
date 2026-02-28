from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from buma.core.config import Settings, get_settings


@lru_cache
def _engine(db_url: str):
    """
    Create (and cache) a SQLAlchemy AsyncEngine for a given database URL.

    What it does:
    - Builds a single `AsyncEngine` per unique `db_url`.
    - Because engine creation is relatively expensive (dialect setup + connection pool),
      caching avoids recreating the engine on every request.

    Why @lru_cache matters here:
    - `@lru_cache` memoizes the function by its arguments.
    - So `_engine("postgresql+asyncpg://...")` is created once, then reused.
    - If you call `_engine()` again with the same `db_url`, you get the same engine object.

    Parameters:
    - db_url (str): Async SQLAlchemy database URL (e.g., "postgresql+asyncpg://...").

    Notable options:
    - pool_pre_ping=True:
        * Before using a pooled connection, SQLAlchemy "pings" it.
        * Helps avoid failures from stale/broken connections after network hiccups or idle time.
    """
    return create_async_engine(db_url, pool_pre_ping=True)


@lru_cache
def _session_factory(db_url: str):
    """
    Create (and cache) an async_sessionmaker bound to the cached engine for `db_url`.

    What it does:
    - Returns an `async_sessionmaker`, which is a *factory* used to create `AsyncSession` objects.
    - This is cheaper than creating engines, but still useful to cache so you build it once.

    Why it calls _engine(db_url):
    - Ensures the sessionmaker is bound to the same cached engine instance for that URL.

    Parameters:
    - db_url (str): Async SQLAlchemy database URL.

    Key option:
    - expire_on_commit=False:
        * By default, SQLAlchemy may "expire" ORM instances on commit, meaning attribute access
          can trigger a lazy reload from the DB.
        * Setting False keeps loaded attributes available after commit, reducing surprise reloads.
          (This is a convenience choice; not strictly required.)
    """
    return async_sessionmaker(_engine(db_url), expire_on_commit=False)


async def get_db(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a per-request SQLAlchemy AsyncSession.

    What it does:
    - Uses FastAPI DI to inject `settings` (resolved by calling `get_settings()` at runtime).
    - Uses the cached sessionmaker for `settings.database_url`.
    - Creates a new `AsyncSession` for the request.
    - Yields that session to the endpoint/service.
    - Ensures session cleanup (close) when the request is done via `async with`.

    Return type (AsyncGenerator[AsyncSession, None]):
    - This is an async generator dependency (`async def` + `yield`).
    - `AsyncGenerator[AsyncSession, None]` means:
        * It yields `AsyncSession` objects (the dependency value).
        * It does not accept any sent-in values (`None` is the "send" type).
    - FastAPI treats code before `yield` as setup and code after `yield` / context exit as teardown.
    - AsyncSession supports being used as an async context manager so that when you exit the block.
    - FastAPI/SQLAlchemy will close the session cleanly (release connection back to the pool, etc.).

    Complex structure explained:
    - `settings: Annotated[Settings, Depends(get_settings)]`:
        * `Settings` is the type.
        * `Depends(get_settings)` is FastAPI metadata: “call `get_settings()` to supply this.”
        * `Annotated[...]` is the standard Python carrier for that metadata.
    - `_session_factory(settings.database_url)()`:
        * `_session_factory(...)` returns an `async_sessionmaker` (a factory).
        * The trailing `()` calls the factory to create an `AsyncSession`.
    - `async with ... as session:`:
        * Ensures the session is closed automatically after the request, even on exceptions.

    Important behavioral note:
    - This dependency does not auto-commit or auto-rollback. Transaction boundaries are controlled
      by your endpoint/service code (or by adding explicit commit/rollback logic here if desired).
    """
    async with _session_factory(settings.database_url)() as session:
        yield session


async def get_redis(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency that provides an async Redis client for the duration of a request.

    What it does:
    - Uses FastAPI DI to inject `settings` (resolved by calling `get_settings()` at runtime).
    - Creates a Redis asyncio client from `settings.redis_url`.
    - Yields the client to the route/consumer.
    - Guarantees cleanup by closing the client in `finally` after the request completes
        (whether success, error, or cancellation).

    Return type (AsyncGenerator[aioredis.Redis, None]):
    - This function is an *async generator dependency* (it uses `yield` inside `async def`).
    - `AsyncGenerator[aioredis.Redis, None]` means:
        * The values it yields are `aioredis.Redis` instances (the dependency value).
        * It does not expect any values to be sent back into the generator (`None` is the "send" type).
        FastAPI uses this pattern to run setup code before `yield` and teardown code after.

    Other notable structures:
    - `settings: Annotated[Settings, Depends(get_settings)]`:
        * `Settings` is the type.
        * `Depends(get_settings)` is FastAPI metadata telling it *how* to supply the value.
        * `Annotated[...]` is the Python mechanism that carries that metadata.
    - `aioredis.from_url(..., decode_responses=True)`:
        * Builds an asyncio-capable Redis client from the URL.
        * `decode_responses=True` makes Redis return `str` instead of `bytes`, which is convenient
            for JSON/text values and reduces manual decoding.
    - `try: yield client  finally: await client.aclose()`:
        * Ensures the client is always closed (even if the endpoint raises).
        * `await client.aclose()` is the async close method for redis asyncio client.
    """
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
