"""
Unit tests for authentication security primitives
(:mod:`app.auth.security`).
"""

from __future__ import annotations

import pytest

from app.auth.exceptions import AuthenticationError
from app.auth.security import (
    create_access_token,
    decode_access_token,
    get_secret_key,
    hash_password,
    verify_password,
)

_SECRET = "unit-test-secret-key-0123456789abcdef0123456789abcdef"


class TestPasswordHashing:
    def test_hash_and_verify_roundtrip(self):
        hashed = hash_password("correct-horse-battery")

        assert hashed != "correct-horse-battery"
        assert verify_password("correct-horse-battery", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct-horse-battery")

        assert verify_password("wrong-password", hashed) is False

    def test_salts_are_unique_per_call(self):
        first = hash_password("same-password")
        second = hash_password("same-password")

        # Same plaintext must never produce the same stored digest.
        assert first != second

        # ... yet both verify correctly.
        assert verify_password("same-password", first)
        assert verify_password("same-password", second)

    def test_malformed_hash_is_rejected(self):
        assert verify_password("anything", "not-a-valid-hash") is False
        assert verify_password("anything", "") is False

    def test_empty_password_is_rejected(self):
        with pytest.raises(ValueError):
            hash_password("")

    def test_unsupported_algorithm_in_stored_hash(self):
        forged = "pbkdf2_sha1$240000$00$00"

        assert verify_password("anything", forged) is False


class TestAccessToken:
    def test_roundtrip_returns_subject(self):
        token = create_access_token("user-123", _SECRET, expires_minutes=5)

        assert isinstance(token, str)
        assert decode_access_token(token, _SECRET) == "user-123"

    def test_wrong_secret_is_rejected(self):
        token = create_access_token("user-123", _SECRET, expires_minutes=5)

        with pytest.raises(AuthenticationError):
            decode_access_token(token, "a-completely-different-secret-key-0123456789abcdef")

    def test_expired_token_is_rejected(self):
        token = create_access_token("user-123", _SECRET, expires_minutes=-1)

        with pytest.raises(AuthenticationError):
            decode_access_token(token, _SECRET)

    def test_tampered_token_is_rejected(self):
        token = create_access_token("user-123", _SECRET, expires_minutes=5)

        header, payload, signature = token.split(".")

        tampered = f"{header}.{payload}.{'0' if signature[0] != '0' else '1'}{signature[1:]}"

        with pytest.raises(AuthenticationError):
            decode_access_token(tampered, _SECRET)

    def test_garbage_token_is_rejected(self):
        with pytest.raises(AuthenticationError):
            decode_access_token("garbage.token.value", _SECRET)


class TestSecretFallback:
    def test_ephemeral_secret_is_stable_within_process(self):
        # Missing configuration falls back to a per-process random secret so
        # development works out of the box.
        assert get_secret_key("") == get_secret_key("")

    def test_configured_secret_takes_precedence(self):
        assert get_secret_key("explicit") == "explicit"

