from __future__ import annotations
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from app.auth.exceptions import AuthenticationError
_PBKDF2_ITERATIONS = 240_000
_HASH_NAME = "pbkdf2_sha256"
_JWT_ALGORITHM = "HS256"
_EPHEMERAL_SECRET = secrets.token_hex(32)
def get_secret_key(configured_secret: str) -> str:
    return configured_secret or _EPHEMERAL_SECRET
def hash_password(password: str) -> str:
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
def create_access_token(
    subject: str,
    secret_key: str,
    expires_minutes: int = 60,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, get_secret_key(secret_key), algorithm=_JWT_ALGORITHM)
def decode_access_token(token: str, secret_key: str) -> str:
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