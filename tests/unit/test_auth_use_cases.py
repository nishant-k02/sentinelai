from __future__ import annotations

import pytest

from sentinelai.modules.auth import use_cases
from sentinelai.modules.auth.models import Role
from sentinelai.modules.auth.use_cases import (
    TokenReuseDetectedError,
    authenticate_user,
    refresh_access_token,
    register_user,
    revoke_refresh_token,
)
from sentinelai.platform.config import Settings
from sentinelai.platform.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from sentinelai.platform.security import decode_access_token, hash_refresh_token, verify_password
from tests.fakes import FakeOrganizationRepository, FakeRefreshTokenRepository, FakeUserRepository

EMAIL = "alice@example.com"
PASSWORD = "correct horse battery staple"


async def _world() -> tuple[Settings, FakeUserRepository, FakeRefreshTokenRepository]:
    org_repo = FakeOrganizationRepository()
    user_repo = FakeUserRepository()
    org = await org_repo.create(name="acme")
    await register_user(
        org_repo,
        user_repo,
        organization_id=org.id,
        email=EMAIL,
        password=PASSWORD,
        role=Role.RESPONDER,
    )
    return Settings(), user_repo, FakeRefreshTokenRepository()


# --- register_user -----------------------------------------------------------


async def test_register_rejects_unknown_organization() -> None:
    import uuid

    with pytest.raises(NotFoundError):
        await register_user(
            FakeOrganizationRepository(),
            FakeUserRepository(),
            organization_id=uuid.uuid4(),
            email=EMAIL,
            password=PASSWORD,
            role=Role.VIEWER,
        )


async def test_register_normalizes_email_and_hashes_password() -> None:
    org_repo, user_repo = FakeOrganizationRepository(), FakeUserRepository()
    org = await org_repo.create(name="acme")

    user = await register_user(
        org_repo,
        user_repo,
        organization_id=org.id,
        email="  Alice@Example.COM ",
        password=PASSWORD,
        role=Role.VIEWER,
    )

    assert user.email == "alice@example.com"
    assert user.password_hash != PASSWORD
    assert verify_password(PASSWORD, user.password_hash)


async def test_register_rejects_duplicate_email_case_insensitively() -> None:
    org_repo, user_repo = FakeOrganizationRepository(), FakeUserRepository()
    org = await org_repo.create(name="acme")
    await register_user(
        org_repo,
        user_repo,
        organization_id=org.id,
        email="Alice@Example.com",
        password=PASSWORD,
        role=Role.VIEWER,
    )
    with pytest.raises(ConflictError):
        await register_user(
            org_repo,
            user_repo,
            organization_id=org.id,
            email="alice@example.com",
            password=PASSWORD,
            role=Role.VIEWER,
        )


@pytest.mark.parametrize("password", ["short", "x" * 11, "x" * 129])
async def test_register_enforces_the_password_policy(password: str) -> None:
    """The use case enforces it too, not just the request schema: the
    bootstrap CLI never goes through HTTP."""
    org_repo, user_repo = FakeOrganizationRepository(), FakeUserRepository()
    org = await org_repo.create(name="acme")

    with pytest.raises(ValidationError):
        await register_user(
            org_repo,
            user_repo,
            organization_id=org.id,
            email=EMAIL,
            password=password,
            role=Role.VIEWER,
        )


# --- authenticate_user -------------------------------------------------------


async def test_authenticate_issues_a_token_pair_with_correct_claims() -> None:
    settings, user_repo, token_repo = await _world()
    user = await user_repo.get_by_email(EMAIL)
    assert user is not None

    pair = await authenticate_user(settings, user_repo, token_repo, email=EMAIL, password=PASSWORD)

    claims = decode_access_token(settings, pair.access_token)
    assert claims["sub"] == str(user.id)
    assert claims["org_id"] == str(user.organization_id)
    assert claims["role"] == "responder"


async def test_refresh_token_is_stored_hashed_never_raw() -> None:
    settings, user_repo, token_repo = await _world()
    pair = await authenticate_user(settings, user_repo, token_repo, email=EMAIL, password=PASSWORD)

    stored = await token_repo.get_by_token_hash(hash_refresh_token(pair.refresh_token))
    assert stored is not None
    assert stored.token_hash != pair.refresh_token


async def test_login_email_is_case_insensitive() -> None:
    settings, user_repo, token_repo = await _world()
    pair = await authenticate_user(
        settings, user_repo, token_repo, email="ALICE@example.com", password=PASSWORD
    )
    assert pair.access_token


async def test_unknown_email_and_wrong_password_are_indistinguishable() -> None:
    settings, user_repo, token_repo = await _world()

    with pytest.raises(AuthenticationError) as unknown:
        await authenticate_user(
            settings, user_repo, token_repo, email="nobody@example.com", password=PASSWORD
        )
    with pytest.raises(AuthenticationError) as wrong:
        await authenticate_user(settings, user_repo, token_repo, email=EMAIL, password="wrong")

    assert str(unknown.value) == str(wrong.value)
    assert unknown.value.code == wrong.value.code


async def test_unknown_email_still_burns_a_password_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests the mechanism, not the timing (timing assertions are flaky)."""
    settings, user_repo, token_repo = await _world()
    calls = 0
    real = verify_password

    def spy(password: str, password_hash: str) -> bool:
        nonlocal calls
        calls += 1
        return real(password, password_hash)

    monkeypatch.setattr(use_cases, "verify_password", spy)

    with pytest.raises(AuthenticationError):
        await authenticate_user(
            settings, user_repo, token_repo, email="nobody@example.com", password="whatever"
        )
    assert calls == 1


# --- refresh_access_token ----------------------------------------------------


async def test_refresh_rotates_the_token() -> None:
    settings, user_repo, token_repo = await _world()
    first = await authenticate_user(settings, user_repo, token_repo, email=EMAIL, password=PASSWORD)

    second = await refresh_access_token(
        settings, user_repo, token_repo, refresh_token=first.refresh_token
    )

    assert second.refresh_token != first.refresh_token
    old = await token_repo.get_by_token_hash(hash_refresh_token(first.refresh_token))
    assert old is not None and old.revoked_at is not None


async def test_refresh_rejects_an_unknown_token() -> None:
    settings, user_repo, token_repo = await _world()
    with pytest.raises(AuthenticationError):
        await refresh_access_token(
            settings, user_repo, token_repo, refresh_token="not-a-real-token"
        )


async def test_refresh_rejects_an_expired_token_without_treating_it_as_theft() -> None:
    _, user_repo, token_repo = await _world()
    expired_settings = Settings(jwt_refresh_token_ttl_seconds=-1)
    pair = await authenticate_user(
        expired_settings, user_repo, token_repo, email=EMAIL, password=PASSWORD
    )

    with pytest.raises(AuthenticationError) as exc_info:
        await refresh_access_token(
            expired_settings, user_repo, token_repo, refresh_token=pair.refresh_token
        )
    assert not isinstance(exc_info.value, TokenReuseDetectedError)


async def test_reuse_of_a_rotated_token_revokes_every_session() -> None:
    settings, user_repo, token_repo = await _world()
    first = await authenticate_user(settings, user_repo, token_repo, email=EMAIL, password=PASSWORD)
    second = await refresh_access_token(
        settings, user_repo, token_repo, refresh_token=first.refresh_token
    )

    with pytest.raises(TokenReuseDetectedError):
        await refresh_access_token(
            settings, user_repo, token_repo, refresh_token=first.refresh_token
        )

    # The legitimately-rotated token is dead too: the whole family is revoked.
    with pytest.raises(AuthenticationError):
        await refresh_access_token(
            settings, user_repo, token_repo, refresh_token=second.refresh_token
        )


# --- revoke_refresh_token (logout) ------------------------------------------


async def test_logout_revokes_the_token() -> None:
    settings, user_repo, token_repo = await _world()
    pair = await authenticate_user(settings, user_repo, token_repo, email=EMAIL, password=PASSWORD)

    await revoke_refresh_token(token_repo, refresh_token=pair.refresh_token)

    with pytest.raises(AuthenticationError):
        await refresh_access_token(
            settings, user_repo, token_repo, refresh_token=pair.refresh_token
        )


async def test_logout_with_an_unknown_token_is_a_silent_no_op() -> None:
    _, _, token_repo = await _world()
    await revoke_refresh_token(token_repo, refresh_token="never-existed")  # must not raise


async def test_double_logout_does_not_revoke_other_sessions() -> None:
    settings, user_repo, token_repo = await _world()
    laptop = await authenticate_user(
        settings, user_repo, token_repo, email=EMAIL, password=PASSWORD
    )
    phone = await authenticate_user(settings, user_repo, token_repo, email=EMAIL, password=PASSWORD)

    await revoke_refresh_token(token_repo, refresh_token=laptop.refresh_token)
    await revoke_refresh_token(token_repo, refresh_token=laptop.refresh_token)  # double-click

    # The phone session survives: logout of a dead token is NOT reuse detection.
    refreshed = await refresh_access_token(
        settings, user_repo, token_repo, refresh_token=phone.refresh_token
    )
    assert refreshed.access_token
