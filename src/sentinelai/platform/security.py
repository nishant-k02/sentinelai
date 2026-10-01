from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import TypedDict

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from sentinelai.platform.config import Settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Argon2id hash — a unique salt is generated and embedded in the
    output automatically; there's nothing else to manage."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Never compare hashes yourself with `==` — that's exactly the kind of
    hand-rolled mistake a vetted library exists to prevent."""
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


class AccessTokenClaims(TypedDict):
    sub: str
    org_id: str
    role: str
    exp: int
    iat: int


def create_access_token(
    settings: Settings, *, user_id: uuid.UUID, organization_id: uuid.UUID, role: str
) -> str:
    now = datetime.now(UTC)
    claims: AccessTokenClaims = {
        "sub": str(user_id),
        "org_id": str(organization_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.jwt_access_token_ttl_seconds)).timestamp()),
    }
    return jwt.encode(dict(claims), settings.jwt_secret, algorithm="HS256")


def decode_access_token(settings: Settings, token: str) -> AccessTokenClaims:
    """Raises a jwt.InvalidTokenError subclass (ExpiredSignatureError,
    InvalidSignatureError, ...) on anything wrong — bad signature, wrong
    secret, expired. Stays framework-agnostic, like everything else in
    platform/; callers (Auth-5) translate that into an AuthenticationError
    at the API boundary."""
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return AccessTokenClaims(
        sub=payload["sub"],
        org_id=payload["org_id"],
        role=payload["role"],
        exp=payload["exp"],
        iat=payload["iat"],
    )


def generate_refresh_token() -> str:
    """A high-entropy opaque secret — not a JWT, carries no claims, exists
    purely as a lookup key into the refresh_tokens table."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """SHA-256, not Argon2 — deliberately. Argon2's slowness defends
    against guessing a *low-entropy* human password; a 32-byte random
    token can't be meaningfully guessed regardless of hash speed. We hash
    it only so a database leak doesn't hand over directly-usable tokens —
    a fast hash is the right tool for that job, not an artificially slow
    one."""
    return hashlib.sha256(token.encode()).hexdigest()
