"""
Password Hashing & JWT Tokens

Security primitives for the authentication layer.

Design Decisions:
    - **PBKDF2-HMAC-SHA256 password hashing**: Implemented with the standard
      library (:func:`hashlib.pbkdf2_hmac`) so no native build dependencies
      (bcrypt/argon2 C extensions) are required. Passwords are never stored
      in plaintext; only the salted, iterated digest is persisted.
    - **Constant-time verification**: Digest comparison uses
      :func:`hmac.compare_digest` to prevent timing attacks.
    - **HS256 JWT access tokens**: Signed with ``AUTH_SECRET_KEY`` and a
      short expiry (``ACCESS_TOKEN_EXPIRE_MINUTES``). Tokens carry the user
      id as the ``sub`` claim plus ``iat``/``exp`` timestamps.
    - **Ephemeral dev secret fallback**: When ``AUTH_SECRET_KEY`` is not
      configured a process-random secret is used so local development works
      out of the box; tokens then invalidate on restart. Production MUST set
      an explicit ``AUTH_SECRET_KEY``.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.auth.exceptions import AuthenticationError

# PBKDF2 iteration count (OWASP recommends >= 600k for PBKDF2-HMAC-SHA256;
# 240k keeps interactive logins responsive while remaining far beyond
# brute-force reach for high-entropy passwords).
_PBKDF2_ITERATIONS = 240_000

_HASH_NAME = "pbkdf2_sha256"

_JWT_ALGORITHM = "HS256"

# Ephemeral per-process secret used when AUTH_SECRET_KEY is not configured.
_EPHEMERAL_SECRET = secrets.token_hex(32)


def get_secret_key(configured_secret: str) -> str:
    """Return the configured signing secret or an ephemeral fallback."""
    return configured_secret or _EPHEMERAL_SECRET


# ──────────────────────────────────────────────────────────────────────────────
# Password hashing
# ──────────────────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """
    Hash a plaintext password with PBKDF2-HMAC-SHA256 and a random salt.

    Args:
        password: The plaintext password.

    Returns:
        A self-describing hash string of the form
        ``pbkdf2_sha256$<iterations>$<salt_b64>$<digest_b64>``.
    """
    if not password:
        raise ValueError("Password must not be empty.")

    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )

    return "$".join(
        [
            _HASH_NAME,
            str(_PBKDF2_ITERATIONS),
            salt.hex(),
            digest.hex(),
        ]
    )


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored hash.

    Uses constant-time comparison so verification timing does not leak
    information about the stored digest.
    """
    try:
        algorithm, iterations_raw, salt_hex, digest_hex = hashed_password.split("$")
    except ValueError:
        return False

    if algorithm != _HASH_NAME:
        return False

    try:
        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )

    return hmac.compare_digest(candidate, expected)


# ──────────────────────────────────────────────────────────────────────────────
# JWT access tokens
# ──────────────────────────────────────────────────────────────────────────────


def create_access_token(
    subject: str,
    secret_key: str,
    expires_minutes: int = 60,
) -> str:
    """
    Mint a signed HS256 access token for a user.

    Args:
        subject: The user id placed in the ``sub`` claim.
        secret_key: The signing secret.
        expires_minutes: Token lifetime in minutes.

    Returns:
        The encoded JWT string.
    """
    now = datetime.now(timezone.utc)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": uuid.uuid4().hex,
    }

    return jwt.encode(payload, get_secret_key(secret_key), algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> str:
    """
    Validate an access token and return its subject (user id).

    Args:
        token: The encoded JWT string.
        secret_key: The signing secret.

    Returns:
        The ``sub`` claim (user id).

    Raises:
        AuthenticationError: When the token is expired, tampered with or
            otherwise invalid.
    """
    try:
        payload = jwt.decode(
            token,
            get_secret_key(secret_key),
            algorithms=[_JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Access token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Could not validate credentials.") from exc

    subject = payload.get("sub")

    if not subject:
        raise AuthenticationError("Could not validate credentials.")

    return str(subject)