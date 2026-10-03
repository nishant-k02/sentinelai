from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update

from sentinelai.modules.auth.models import RefreshToken, User
from sentinelai.platform.repository import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


class RefreshTokenRepository(SQLAlchemyRepository[RefreshToken]):
    model = RefreshToken

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_if_active(self, token_id: uuid.UUID) -> bool:
        """Atomically flip a token active -> revoked. True only for the one
        caller that actually performed the flip.

        This is a single conditional UPDATE, not 'read revoked_at, then
        write it'. Under READ COMMITTED, a second concurrent UPDATE blocks
        on the row lock, then re-evaluates its WHERE clause against the
        now-updated row, matches nothing, and returns no row. Two
        simultaneous refreshes with the same token cannot both win.
        """
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .returning(RefreshToken.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
