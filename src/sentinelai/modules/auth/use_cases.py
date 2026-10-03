from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Protocol

from sentinelai.modules.auth.models import RefreshToken, Role, User
from sentinelai.platform.config import Settings
from sentinelai.platform.errors import AuthenticationError, ConflictError, NotFoundError
from sentinelai.platform.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


class TokenReuseDetectedError(AuthenticationError):
    """A revoked refresh token was presented again. The use case has already
    revoked every session for that user, and that side effect MUST be
    persisted, but raising rolls back the request's transaction. The route
    catches this, commits explicitly, then lets a plain 401 through. See
    the refresh route (Auth-4)."""


# Defined here, not imported from modules/service: the independence
# contract forbids it, and each consumer owning the one-method interface
# it needs is the whole point of consumer-defined protocols.
class OrganizationLookupProtocol(Protocol):
    async def get(self, id: uuid.UUID) -> object | None: ...


class UserRepositoryProtocol(Protocol):
    async def get(self, id: uuid.UUID) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...
    async def create(self, **fields: object) -> User: ...


class RefreshTokenRepositoryProtocol(Protocol):
    async def create(self, **fields: object) -> RefreshToken: ...
    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None: ...
    async def revoke_if_active(self, token_id: uuid.UUID) -> bool: ...
    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None: ...


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str  # raw value: returned to the client once, never stored
    expires_in: int


_INVALID_CREDENTIALS = "invalid email or password"
_INVALID_REFRESH = "invalid refresh token"


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@lru_cache
def _dummy_password_hash() -> str:
    return hash_password("dummy-password-for-timing-equalization")


async def _hash_password(password: str) -> str:
    # Argon2 is synchronous and takes tens of ms. Called directly in an
    # async handler it would block every other request on this worker.
    return await asyncio.to_thread(hash_password, password)


async def _verify_password(password: str, password_hash: str) -> bool:
    return await asyncio.to_thread(verify_password, password, password_hash)


async def _issue_token_pair(
    settings: Settings, token_repo: RefreshTokenRepositoryProtocol, user: User
) -> TokenPair:
    access = create_access_token(
        settings, user_id=user.id, organization_id=user.organization_id, role=user.role.value
    )
    raw_refresh = generate_refresh_token()
    await token_repo.create(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_token_ttl_seconds),
    )
    return TokenPair(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.jwt_access_token_ttl_seconds,
    )


async def register_user(
    org_repo: OrganizationLookupProtocol,
    user_repo: UserRepositoryProtocol,
    *,
    organization_id: uuid.UUID,
    email: str,
    password: str,
    role: Role,
) -> User:
    """Create a user in an organization.

    This is a pure domain operation with NO authorization logic. WHO may
    call it is the caller's job: the API exposes it admin-only, with the
    organization taken from the caller's token (Auth-4), and the bootstrap
    command calls it directly. Putting auth rules here would make the
    bootstrap path impossible.

    Known trade-off: a 409 on a duplicate email reveals that the address is
    registered (user enumeration). The standard fix, always answering
    'check your email' and sending a message, needs email infrastructure
    we don't have. Recorded in SECURITY.md (Auth-6).
    """
    if await org_repo.get(organization_id) is None:
        raise NotFoundError(f"organization {organization_id} not found")

    normalized = _normalize_email(email)
    if await user_repo.get_by_email(normalized) is not None:
        raise ConflictError("a user with this email already exists")

    return await user_repo.create(
        organization_id=organization_id,
        email=normalized,
        password_hash=await _hash_password(password),
        role=role,
    )


async def authenticate_user(
    settings: Settings,
    user_repo: UserRepositoryProtocol,
    token_repo: RefreshTokenRepositoryProtocol,
    *,
    email: str,
    password: str,
) -> TokenPair:
    user = await user_repo.get_by_email(_normalize_email(email))
    if user is None:
        # Burn a comparable amount of time as a real verification, so
        # response time doesn't reveal whether this email is registered.
        await _verify_password(password, await asyncio.to_thread(_dummy_password_hash))
        raise AuthenticationError(_INVALID_CREDENTIALS)

    if not await _verify_password(password, user.password_hash):
        raise AuthenticationError(_INVALID_CREDENTIALS)  # same message as above, on purpose

    return await _issue_token_pair(settings, token_repo, user)


async def refresh_access_token(
    settings: Settings,
    user_repo: UserRepositoryProtocol,
    token_repo: RefreshTokenRepositoryProtocol,
    *,
    refresh_token: str,
) -> TokenPair:
    stored = await token_repo.get_by_token_hash(hash_refresh_token(refresh_token))
    if stored is None:
        raise AuthenticationError(_INVALID_REFRESH)

    if stored.revoked_at is not None:
        # A dead token is being presented: a stale client, or a thief
        # holding a copy. We can't tell which, so treat it as compromise.
        await token_repo.revoke_all_for_user(stored.user_id)
        raise TokenReuseDetectedError(_INVALID_REFRESH)

    if stored.expires_at <= datetime.now(UTC):
        raise AuthenticationError(_INVALID_REFRESH)  # expiry is not theft

    # Rotation. The atomic claim is what makes this race-free: only one
    # concurrent caller can flip active -> revoked. A loser presented the
    # same token as the winner, which is reuse by definition.
    if not await token_repo.revoke_if_active(stored.id):
        await token_repo.revoke_all_for_user(stored.user_id)
        raise TokenReuseDetectedError(_INVALID_REFRESH)

    user = await user_repo.get(stored.user_id)
    if user is None:
        raise AuthenticationError(_INVALID_REFRESH)

    return await _issue_token_pair(settings, token_repo, user)


async def revoke_refresh_token(
    token_repo: RefreshTokenRepositoryProtocol, *, refresh_token: str
) -> None:
    """Logout. Idempotent: an unknown or already-revoked token is a silent
    no-op, so a double-clicked logout doesn't nuke every session (unlike
    refresh, where presenting a dead token IS suspicious) and the response
    never reveals whether a token was valid."""
    stored = await token_repo.get_by_token_hash(hash_refresh_token(refresh_token))
    if stored is not None:
        await token_repo.revoke_if_active(stored.id)
