from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.supabase_db_url,
        pool_pre_ping=True,
        pool_size=10,
        # Supabase's connection pooler (the "Transaction pooler" on port 6543)
        # multiplexes physical connections per-transaction, which is
        # incompatible with asyncpg's default prepared-statement caching --
        # it raises DuplicatePreparedStatementError under any concurrent
        # load. Disabling the statement cache is the standard fix when a
        # pgbouncer-style transaction-mode pooler sits in front of asyncpg.
        connect_args={"statement_cache_size": 0},
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


def new_worker_session() -> AsyncSession:
    """Used by Celery tasks (outside FastAPI's request scope) to get a fresh
    session bound to the current worker process's engine."""
    return get_session_factory()()
