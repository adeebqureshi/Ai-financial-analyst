"""
Authentication Dependencies

FastAPI dependency callables that resolve the caller's identity.

Design Decisions:
    - **Single gate**: ``get_current_user`` is attached to every protected
      router (see ``app.api.routers``) and to individual handlers that need
      the identity for ownership checks. FastAPI caches dependency results
      per request, so the token is decoded only once.
    - **Backward-compatible opt-out**: When ``AUTH_ENABLED`` is false the
      dependency returns ``None`` instead of rejecting the request. This
      keeps existing deployments/tests working unchanged while production
      defaults to secure (``AUTH_ENABLED=true``).
    - **401 vs 403**: Missing/invalid credentials raise
      ``AuthenticationError`` (401); resource-level denials raise
      ``AuthorizationError`` (403).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.auth.database import get_db_session
from app.auth.exceptions import AuthenticationError, AuthorizationError
from app.auth.models import User
from app.auth.security import decode_access_token
from app.auth.service import UserService
from app.core.config import Settings, get_settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# auto_error=False so we control the 401 response shape ourselves.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    auto_error=False,
)


def get_auth_settings() -> Iterator[Settings]:
    """
    FastAPI dependency yielding the application settings.

    Mirrors ``app.api.dependencies.settings.get_settings_dep`` but lives
    inside the auth package so the auth stack has no import-time coupling
    to the API package (which imports the routers that consume these
    dependencies). Overridable via ``app.dependency_overrides``.
    """
    yield get_settings()


def get_auth_db(
    settings: Settings = Depends(get_auth_settings),
) -> Iterator[Session]:
    """FastAPI dependency yielding the authentication database session."""
    yield from get_db_session(settings)


def _resolve_user(
    token: str | None,
    settings: Settings,
    session,
) -> User | None:
    """Shared resolution logic for the current-user dependencies."""
    if not settings.auth_enabled:
        # Authentication disabled: requests proceed anonymously.
        return None

    if not token:
        raise AuthenticationError("Not authenticated.")

    user_id = decode_access_token(token, settings.auth_secret_key_str)

    user = UserService(session).get_by_id(user_id)

    if user is None or not user.is_active:
        raise AuthenticationError("Could not validate credentials.")

    return user


def get_current_user(
    settings: Settings = Depends(get_auth_settings),
    token: str | None = Depends(oauth2_scheme),
    session=Depends(get_auth_db),
) -> User | None:
    """
    Resolve the authenticated user for the request.

    Returns:
        The authenticated ``User``, or ``None`` when authentication is
        disabled via configuration.

    Raises:
        AuthenticationError: When authentication is enabled and the request
            carries no valid bearer token.
    """
    return _resolve_user(token, settings, session)


def require_authenticated_user(
    current_user: User | None = Depends(get_current_user),
) -> User:
    """
    Strict variant used to guard business routers.

    Raises:
        AuthenticationError: When no authenticated user is present.
    """
    if current_user is None:
        raise AuthenticationError("Not authenticated.")

    return current_user


def require_ownership(owner_id: str | None, current_user: User | None) -> None:
    """
    Assert that ``current_user`` owns a resource.

    Args:
        owner_id: The owner recorded on the target resource (``None`` for
            legacy/anonymous resources, which remain accessible).
        current_user: The authenticated user.

    Raises:
        AuthorizationError: When the resource belongs to another user.
    """
    if owner_id is None or current_user is None:
        return

    if owner_id != current_user.id:
        raise AuthorizationError("You do not have access to this resource.")