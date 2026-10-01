from __future__ import annotations

import uuid

import jwt
import pytest

from sentinelai.platform.config import Settings
from sentinelai.platform.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed) is True


def test_password_verify_rejects_wrong_password() -> None:
    hashed = hash_password("correct horse battery staple")
    assert verify_password("wrong password", hashed) is False


def test_password_hash_is_not_the_plaintext() -> None:
    hashed = hash_password("hunter2")
    assert "hunter2" not in hashed


def test_access_token_roundtrip() -> None:
    settings = Settings()
    user_id, org_id = uuid.uuid4(), uuid.uuid4()

    token = create_access_token(settings, user_id=user_id, organization_id=org_id, role="responder")
    claims = decode_access_token(settings, token)

    assert claims["sub"] == str(user_id)
    assert claims["org_id"] == str(org_id)
    assert claims["role"] == "responder"


def test_expired_access_token_is_rejected() -> None:
    settings = Settings(jwt_access_token_ttl_seconds=-1)  # already expired on creation
    token = create_access_token(
        settings, user_id=uuid.uuid4(), organization_id=uuid.uuid4(), role="viewer"
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(settings, token)


def test_tampered_token_signature_is_rejected() -> None:
    settings = Settings()
    token = create_access_token(
        settings, user_id=uuid.uuid4(), organization_id=uuid.uuid4(), role="viewer"
    )
    tampered = token[:-4] + "aaaa"
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(settings, tampered)


def test_token_signed_with_a_different_secret_is_rejected() -> None:
    # >= 32 bytes each -- short of that, PyJWT itself warns
    # (InsecureKeyLengthWarning) regardless of what this test is checking.
    settings_a = Settings(jwt_secret="a" * 32)
    settings_b = Settings(jwt_secret="b" * 32)
    token = create_access_token(
        settings_a, user_id=uuid.uuid4(), organization_id=uuid.uuid4(), role="viewer"
    )
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(settings_b, token)


def test_refresh_token_hash_is_deterministic_and_not_reversible() -> None:
    token = generate_refresh_token()
    assert hash_refresh_token(token) == hash_refresh_token(token)
    assert hash_refresh_token(token) != token


def test_generated_refresh_tokens_are_unique() -> None:
    tokens = {generate_refresh_token() for _ in range(100)}
    assert len(tokens) == 100
