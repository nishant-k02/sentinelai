from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from sentinelai.platform.config import Settings


class Base(DeclarativeBase):
    """Parent of every ORM model.

    ``Base.metadata`` is the schema described in Python. Alembic autogenerate
    diffs it against the live database to produce migration scripts.
    """


def create_db_engine(settings: Settings) -> AsyncEngine:
    """Create the async engine — a lazily-filled pool of PostgreSQL connections.

    One engine per process, shared by all requests.

    - ``pool_size=5`` / ``max_overflow=10`` — up to 5 kept-open connections,
      plus 10 burst connections that are closed when returned. This is a
      *per-replica* limit; at N replicas the DB sees up to N*(5..15).
    - ``pool_pre_ping=True`` — run a cheap ``SELECT 1`` before lending out a
      pooled connection, so a stale/dropped connection becomes a transparent
      reconnect instead of a mid-query error.
    """
    return create_async_engine(
        settings.database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,  # set True to log every SQL statement while learning
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return a factory that makes AsyncSession objects bound to ``engine``.

    A session = one unit of work = one transaction. Open one per request or
    per consumed message, use it, close it. Used from M1 onward.

    ``expire_on_commit=False`` — keep loaded objects usable after ``commit()``
    (otherwise attribute access after commit triggers a fresh query).
    """
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
