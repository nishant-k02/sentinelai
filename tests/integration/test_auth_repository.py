from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sentinelai.modules.auth.models import RefreshToken, Role, User
from sentinelai.modules.auth.repository import RefreshTokenRepository, UserRepository
from sentinelai.platform.config import get_settings
from sentinelai.platform.db import create_db_engine, create_session_factory
from sentinelai.platform.security import generate_refresh_token, hash_refresh_token
from tests.helpers import make_organization

pytestmark = pytest.mark.integration

Factory = async_sessionmaker[AsyncSession]


@pytest.fixture
async def factory() -> AsyncIterator[Factory]:
    engine = create_db_engine(get_settings())
    yield create_session_factory(engine)
    await engine.dispose()


async def _make_user(
    factory: Factory, *, tokens: int = 1
) -> tuple[uuid.UUID, list[tuple[uuid.UUID, str]]]:
    """Returns (user_id, [(token_id, raw_token), ...])."""
    org_id = await make_organization()
    async with factory() as session:
        user = User(
            organization_id=org_id,
            email=f"{uuid.uuid4()}@example.com",
            password_hash="not-a-real-hash",
            role=Role.VIEWER,
        )
        session.add(user)
        await session.flush()

        made: list[tuple[uuid.UUID, str]] = []
        for _ in range(tokens):
            raw = generate_refresh_token()
            token = RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(raw),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
            session.add(token)
            await session.flush()
            made.append((token.id, raw))
        await session.commit()
        return user.id, made


async def test_get_by_email_finds_the_user(factory: Factory) -> None:
    user_id, _ = await _make_user(factory)
    async with factory() as session:
        user = await session.get(User, user_id)
        assert user is not None
        found = await UserRepository(session).get_by_email(user.email)
        assert found is not None and found.id == user_id


async def test_duplicate_email_is_rejected_by_the_database(factory: Factory) -> None:
    """The backstop behind register_user's pre-check, same pattern as services."""
    org_id = await make_organization()
    email = f"{uuid.uuid4()}@example.com"
    async with factory() as session:
        session.add(User(organization_id=org_id, email=email, password_hash="x", role=Role.VIEWER))
        await session.commit()
        session.add(User(organization_id=org_id, email=email, password_hash="y", role=Role.ADMIN))
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


async def test_revoke_if_active_is_true_once_then_false(factory: Factory) -> None:
    _, [(token_id, raw)] = await _make_user(factory)
    async with factory() as session:
        repo = RefreshTokenRepository(session)
        assert await repo.get_by_token_hash(hash_refresh_token(raw)) is not None
        assert await repo.revoke_if_active(token_id) is True
        assert await repo.revoke_if_active(token_id) is False
        await session.commit()


async def test_concurrent_revoke_has_exactly_one_winner(factory: Factory) -> None:
    """Two requests present the same refresh token at the same moment. Exactly
    one may win. This is the real proof of the atomic claim."""
    _, [(token_id, _)] = await _make_user(factory)

    async def attempt() -> bool:
        async with factory() as session:
            won = await RefreshTokenRepository(session).revoke_if_active(token_id)
            await session.commit()
            return won

    results = await asyncio.gather(attempt(), attempt())
    assert sorted(results) == [False, True]


async def test_revoke_all_for_user_revokes_every_active_token(factory: Factory) -> None:
    user_id, made = await _make_user(factory, tokens=2)
    async with factory() as session:
        await RefreshTokenRepository(session).revoke_all_for_user(user_id)
        await session.commit()

    async with factory() as session:
        for token_id, _ in made:
            token = await session.get(RefreshToken, token_id)
            assert token is not None and token.revoked_at is not None
