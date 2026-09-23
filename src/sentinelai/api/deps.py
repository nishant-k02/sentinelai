from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sentinelai.modules.service.repository import ServiceRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request — one transaction boundary per request.
    Commits if the route completes without raising; rolls back and
    re-raises otherwise, so our exception handlers (Phase 0.4) still see
    whatever went wrong."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_service_repository(session: SessionDep) -> ServiceRepository:
    return ServiceRepository(session)


ServiceRepositoryDep = Annotated[ServiceRepository, Depends(get_service_repository)]
