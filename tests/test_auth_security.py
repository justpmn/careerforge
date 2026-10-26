
from datetime import timedelta

import pytest

from src.backend.app.core.config import settings
from src.backend.app.core.security import (
    hash_password,
    verify_password,
)
from src.backend.app.core.tokens import (
    create_access_token,
    decode_access_token,
)


@pytest.fixture(autouse=True)
def configure_test_secret(monkeypatch):
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "careerforge-test-signing-secret-" + "a" * 48,
    )


def test_password_hashing():
    password = "CareerForge-SecurePassword-2026!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash.startswith("$argon2id$")
    assert first_hash != second_hash
    assert first_hash != password
    assert len(first_hash) <= 255


def test_password_verification():
    password = "CareerForge-SecurePassword-2026!"
    stored_hash = hash_password(password)

    assert verify_password(password, stored_hash)
    assert not verify_password("IncorrectPassword", stored_hash)


def test_invalid_password_hash():
    assert not verify_password(
        "CareerForge-SecurePassword-2026!",
        "invalid-hash",
    )

    assert not verify_password(
        "CareerForge-SecurePassword-2026!",
        "CareerForge-SecurePassword-2026!",
    )


def test_empty_password_rejected():
    with pytest.raises(ValueError):
        hash_password("")


def test_access_token_creation():
    token = create_access_token(user_id=2)

    assert isinstance(token, str)
    assert decode_access_token(token) == 2


def test_expired_token_rejected():
    token = create_access_token(
        user_id=2,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_invalid_token_rejected():
    with pytest.raises(ValueError):
        decode_access_token("invalid.jwt.token")


def test_invalid_signature_rejected(monkeypatch):
    token = create_access_token(user_id=2)

    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "different-test-signing-secret-" + "b" * 48,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_invalid_user_id_rejected():
    with pytest.raises(ValueError):
        create_access_token(user_id=-1)


def test_missing_signing_secret_rejected(monkeypatch):
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        None,
    )

    with pytest.raises(RuntimeError):
        create_access_token(user_id=2)
