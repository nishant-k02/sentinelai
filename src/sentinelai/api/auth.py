"""Authentication and authorization as FastAPI dependencies.

Declared on the route signature, so each route states what it requires
right where its parameters are:

    async def create_service(user: ResponderDep, ...) -> ...

Authorization is a pure claims check: decode the access token, verify
signature and expiry, read org_id/role from it. No database round-trip per
request: that is the point of a stateless access token, and the reason it
cannot be revoked before it expires (see Auth-1).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sentinelai.api.deps import SettingsDep
from sentinelai.modules.auth.models import Role
from sentinelai.platform.errors import AuthenticationError, AuthorizationError
from sentinelai.platform.security import decode_access_token

# auto_error=False: we raise our own AuthenticationError so a missing header
# yields the same {"error": {...}} envelope and 401 as every other failure,
# instead of whatever FastAPI's built-in default happens to be.
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    organization_id: uuid.UUID
    role: Role


async def get_current_user(
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser:
    if credentials is None:
        raise AuthenticationError("missing bearer token")
    try:
        claims = decode_access_token(settings, credentials.credentials)
        return CurrentUser(
            id=uuid.UUID(claims["sub"]),
            organization_id=uuid.UUID(claims["org_id"]),
            role=Role(claims["role"]),
        )
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        # One message for every failure mode (bad signature, expired,
        # malformed claims, unknown role): the client's only useful
        # reaction to any of them is the same, "get a fresh token".
        raise AuthenticationError("invalid or expired token") from exc


def require_role(minimum: Role) -> Callable[..., Awaitable[CurrentUser]]:
    """Dependency factory: pass if the caller's role is at least `minimum`.
    Roles are ordered (Role.rank), so ADMIN satisfies a RESPONDER gate."""

    async def dependency(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if user.role.rank < minimum.rank:
            raise AuthorizationError(f"requires role {minimum.value} or higher")
        return user

    return dependency


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
ViewerDep = Annotated[CurrentUser, Depends(require_role(Role.VIEWER))]
ResponderDep = Annotated[CurrentUser, Depends(require_role(Role.RESPONDER))]
AdminDep = Annotated[CurrentUser, Depends(require_role(Role.ADMIN))]
