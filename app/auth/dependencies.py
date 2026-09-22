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
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    auto_error=False,
)
def get_auth_settings() -> Iterator[Settings]:
    yield get_settings()
def get_auth_db(
    settings: Settings = Depends(get_auth_settings),
) -> Iterator[Session]:
    yield from get_db_session(settings)
def _resolve_user(
    token: str | None,
    settings: Settings,
    session,
) -> User | None:
    if not settings.auth_enabled:
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
    return _resolve_user(token, settings, session)
def require_authenticated_user(
    current_user: User | None = Depends(get_current_user),
) -> User:
    if current_user is None:
        raise AuthenticationError("Not authenticated.")
    return current_user
def require_ownership(owner_id: str | None, current_user: User | None) -> None:
    if current_user is None:
        return
    if owner_id is None or owner_id != current_user.id:
        raise AuthorizationError("You do not have access to this resource.")