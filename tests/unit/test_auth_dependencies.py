"""get_current_user / require_role, exercised through a throwaway app.

No database: authorization is a pure claims check, so these run in
milliseconds. The attack tests below are the executable answer to "what
stops a client editing role=viewer to role=admin in the token it holds?"
"""

from __future__ import annotations

import base64
import json
import uuid
from collections.abc import AsyncIterator

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from sentinelai.api.auth import AdminDep, ResponderDep, ViewerDep
from sentinelai.api.errors import register_exception_handlers
from sentinelai.modules.auth.models import Role
from sentinelai.platform.config import Settings
from sentinelai.platform.security import create_access_token

SETTINGS = Settings()


def _make_app() -> FastAPI:
    app = FastAPI()
    app.state.settings = SETTINGS
    register_exception_handlers(app)

    @app.get("/viewer")
    async def viewer(user: ViewerDep) -> dict[str, str]:
        return {"role": user.role.value}

    @app.get("/responder")
    async def responder(user: ResponderDep) -> dict[str, str]:
        return {"role": user.role.value}

    @app.get("/admin")
    async def admin(user: AdminDep) -> dict[str, str]:
        return {"role": user.role.value}

    return app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=_make_app()), base_url="http://test") as c:
        yield c


def _token(role: Role, settings: Settings = SETTINGS) -> str:
    return create_access_token(
        settings, user_id=uuid.uuid4(), organization_id=uuid.uuid4(), role=role.value
    )


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _b64(data: dict[str, object]) -> str:
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


@pytest.mark.parametrize(
    ("role", "path", "expected"),
    [
        (Role.VIEWER, "/viewer", 200),
        (Role.VIEWER, "/responder", 403),
        (Role.VIEWER, "/admin", 403),
        (Role.RESPONDER, "/viewer", 200),
        (Role.RESPONDER, "/responder", 200),
        (Role.RESPONDER, "/admin", 403),
        (Role.ADMIN, "/viewer", 200),
        (Role.ADMIN, "/responder", 200),
        (Role.ADMIN, "/admin", 200),
    ],
)
async def test_role_matrix(client: AsyncClient, role: Role, path: str, expected: int) -> None:
    resp = await client.get(path, headers=_bearer(_token(role)))
    assert resp.status_code == expected
    if expected == 403:
        assert resp.json()["error"]["code"] == "forbidden"


async def test_missing_token_is_401_with_www_authenticate(client: AsyncClient) -> None:
    resp = await client.get("/viewer")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"
    assert resp.headers["www-authenticate"] == "Bearer"


async def test_garbage_token_is_401(client: AsyncClient) -> None:
    resp = await client.get("/viewer", headers=_bearer("not.a.jwt"))
    assert resp.status_code == 401


async def test_expired_token_is_401(client: AsyncClient) -> None:
    expired = _token(Role.ADMIN, Settings(jwt_access_token_ttl_seconds=-1))
    resp = await client.get("/viewer", headers=_bearer(expired))
    assert resp.status_code == 401


async def test_token_signed_with_another_secret_is_401(client: AsyncClient) -> None:
    forged = _token(Role.ADMIN, Settings(jwt_secret="attacker-chose-this-secret-0123456789"))
    resp = await client.get("/admin", headers=_bearer(forged))
    assert resp.status_code == 401


async def test_editing_the_role_claim_invalidates_the_signature(client: AsyncClient) -> None:
    """The answer to Auth-1's first question. Take a real VIEWER token,
    swap the payload for one claiming ADMIN, keep the original signature."""
    header, payload, signature = _token(Role.VIEWER).split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["role"] = "admin"
    tampered = f"{header}.{_b64(claims)}.{signature}"

    resp = await client.get("/admin", headers=_bearer(tampered))
    assert resp.status_code == 401  # not 403: it never got as far as the role


async def test_alg_none_token_is_rejected(client: AsyncClient) -> None:
    """The classic JWT attack: declare `alg: none`, send no signature, hope
    the server believes the header. Safe because decode pins algorithms=[HS256]."""
    claims = {
        "sub": str(uuid.uuid4()),
        "org_id": str(uuid.uuid4()),
        "role": "admin",
        "iat": 0,
        "exp": 4_102_444_800,  # year 2100
    }
    unsigned = f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64(claims)}."
    resp = await client.get("/admin", headers=_bearer(unsigned))
    assert resp.status_code == 401


async def test_validly_signed_token_with_unknown_role_is_401(client: AsyncClient) -> None:
    claims = {
        "sub": str(uuid.uuid4()),
        "org_id": str(uuid.uuid4()),
        "role": "superuser",
        "iat": 0,
        "exp": 4_102_444_800,
    }
    token = jwt.encode(claims, SETTINGS.jwt_secret, algorithm="HS256")
    resp = await client.get("/viewer", headers=_bearer(token))
    assert resp.status_code == 401
