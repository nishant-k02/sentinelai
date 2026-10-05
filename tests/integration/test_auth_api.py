from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient, Response

from sentinelai.modules.auth.models import Role
from sentinelai.platform.config import get_settings
from sentinelai.platform.redis import create_redis
from tests.helpers import TEST_PASSWORD, make_organization, make_user

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def _clean_login_rate_limits() -> AsyncIterator[None]:
    """Login counters live in Redis for 15 minutes and key on client IP, which
    is always 127.0.0.1 in tests. Without this, repeated test runs would
    accumulate toward the per-IP limit and start failing with 429."""
    redis = create_redis(get_settings())

    async def wipe() -> None:
        async for key in redis.scan_iter("ratelimit:login:*"):
            await redis.delete(key)

    await wipe()
    yield
    await wipe()
    await redis.aclose()


async def _login(client: AsyncClient, email: str, password: str = TEST_PASSWORD) -> Response:
    return await client.post("/v1/auth/login", json={"email": email, "password": password})


def _auth(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _login_tokens(client: AsyncClient, email: str) -> dict[str, Any]:
    resp = await _login(client, email)
    assert resp.status_code == 200, resp.text
    tokens: dict[str, Any] = resp.json()
    return tokens


# --- login / me --------------------------------------------------------------


async def test_login_issues_tokens_and_me_returns_the_user(live_client: AsyncClient) -> None:
    org_id = await make_organization()
    email = await make_user(org_id, role=Role.RESPONDER)

    tokens = await _login_tokens(live_client, email)
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == get_settings().jwt_access_token_ttl_seconds

    me = await live_client.get("/v1/me", headers=_auth(tokens))
    assert me.status_code == 200
    assert me.json()["email"] == email
    assert me.json()["role"] == "responder"
    assert me.json()["organization_id"] == str(org_id)
    assert "password" not in me.text  # neither the password nor its hash is ever serialized


async def test_me_without_a_token_is_401(live_client: AsyncClient) -> None:
    resp = await live_client.get("/v1/me")
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"


async def test_wrong_password_and_unknown_email_are_indistinguishable(
    live_client: AsyncClient,
) -> None:
    email = await make_user(await make_organization())

    wrong_password = await _login(live_client, email, "definitely the wrong password")
    unknown_email = await _login(live_client, f"{uuid.uuid4()}@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


# --- refresh / logout --------------------------------------------------------


async def test_refresh_rotates_the_token(live_client: AsyncClient) -> None:
    email = await make_user(await make_organization())
    first = await _login_tokens(live_client, email)

    resp = await live_client.post(
        "/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )

    assert resp.status_code == 200
    assert resp.json()["refresh_token"] != first["refresh_token"]


async def test_reusing_a_rotated_token_revokes_every_session_and_that_persists(
    live_client: AsyncClient,
) -> None:
    """The regression test for the commit-before-raise design.

    Reuse detection revokes ALL of the user's tokens and then raises 401.
    Raising makes get_session roll the transaction back. If the route did
    not commit first, the revocation would silently vanish and the NEWEST
    token below would still work (200). It must be dead (401)."""
    email = await make_user(await make_organization())
    first = await _login_tokens(live_client, email)

    rotated = await live_client.post(
        "/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert rotated.status_code == 200
    newest = rotated.json()

    replay = await live_client.post(
        "/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert replay.status_code == 401

    after = await live_client.post(
        "/v1/auth/refresh", json={"refresh_token": newest["refresh_token"]}
    )
    assert after.status_code == 401


async def test_logout_revokes_the_refresh_token(live_client: AsyncClient) -> None:
    email = await make_user(await make_organization())
    tokens = await _login_tokens(live_client, email)

    out = await live_client.post("/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert out.status_code == 204

    resp = await live_client.post(
        "/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 401


async def test_logout_with_an_unknown_token_still_succeeds(live_client: AsyncClient) -> None:
    resp = await live_client.post("/v1/auth/logout", json={"refresh_token": "never-existed"})
    assert resp.status_code == 204


# --- creating users: admin only, organization from the token ------------------


async def test_admin_creates_a_user_in_their_own_org_who_can_then_log_in(
    live_client: AsyncClient,
) -> None:
    org_id = await make_organization()
    admin = await _login_tokens(live_client, await make_user(org_id, role=Role.ADMIN))
    new_email = f"{uuid.uuid4()}@example.com"

    created = await live_client.post(
        "/v1/users",
        headers=_auth(admin),
        json={"email": new_email, "password": "a perfectly fine passphrase", "role": "viewer"},
    )

    assert created.status_code == 201
    assert created.headers["location"] == f"/v1/users/{created.json()['id']}"
    assert created.json()["organization_id"] == str(org_id)
    assert (await _login(live_client, new_email, "a perfectly fine passphrase")).status_code == 200


async def test_non_admins_cannot_create_users(live_client: AsyncClient) -> None:
    org_id = await make_organization()
    payload = {"email": f"{uuid.uuid4()}@example.com", "password": TEST_PASSWORD, "role": "admin"}

    anonymous = await live_client.post("/v1/users", json=payload)
    assert anonymous.status_code == 401

    # The privilege-escalation attempt this milestone was redesigned around:
    # a responder trying to mint themselves (or a friend) an admin account.
    responder = await _login_tokens(live_client, await make_user(org_id, role=Role.RESPONDER))
    forbidden = await live_client.post("/v1/users", headers=_auth(responder), json=payload)
    assert forbidden.status_code == 403


async def test_create_user_validates_password_length_and_email(live_client: AsyncClient) -> None:
    admin = await _login_tokens(live_client, await make_user(await make_organization()))

    short = await live_client.post(
        "/v1/users",
        headers=_auth(admin),
        json={"email": f"{uuid.uuid4()}@example.com", "password": "too short", "role": "viewer"},
    )
    assert short.status_code == 422
    assert "too short" not in short.text  # the rejected password is never echoed back

    bad_email = await live_client.post(
        "/v1/users",
        headers=_auth(admin),
        json={"email": "not-an-email", "password": TEST_PASSWORD, "role": "viewer"},
    )
    assert bad_email.status_code == 422


async def test_duplicate_email_returns_409(live_client: AsyncClient) -> None:
    admin = await _login_tokens(live_client, await make_user(await make_organization()))
    payload = {"email": f"{uuid.uuid4()}@example.com", "password": TEST_PASSWORD, "role": "viewer"}

    assert (
        await live_client.post("/v1/users", headers=_auth(admin), json=payload)
    ).status_code == 201
    again = await live_client.post("/v1/users", headers=_auth(admin), json=payload)
    assert again.status_code == 409


async def test_an_admin_cannot_see_another_organizations_users(live_client: AsyncClient) -> None:
    admin_a = await _login_tokens(live_client, await make_user(await make_organization()))
    admin_b = await _login_tokens(live_client, await make_user(await make_organization()))

    created = await live_client.post(
        "/v1/users",
        headers=_auth(admin_a),
        json={"email": f"{uuid.uuid4()}@example.com", "password": TEST_PASSWORD, "role": "viewer"},
    )
    user_id = created.json()["id"]

    own = await live_client.get(f"/v1/users/{user_id}", headers=_auth(admin_a))
    assert own.status_code == 200

    # 404, not 403: a 403 would confirm the id exists in someone else's tenant.
    other = await live_client.get(f"/v1/users/{user_id}", headers=_auth(admin_b))
    assert other.status_code == 404


# --- brute-force protection --------------------------------------------------


async def test_login_is_rate_limited_per_ip_and_email(live_client: AsyncClient) -> None:
    email = f"{uuid.uuid4()}@example.com"  # unknown account: the limiter doesn't care

    statuses = [(await _login(live_client, email, "wrong")).status_code for _ in range(11)]

    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429
