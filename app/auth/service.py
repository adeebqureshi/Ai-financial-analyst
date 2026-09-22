from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.exceptions import EmailAlreadyRegisteredError
from app.auth.models import User
from app.auth.security import hash_password, verify_password
from app.core.logging import get_logger
logger = get_logger("app.auth.service")
_LOGIN_FAILURE_REASONS = {
    "unknown_user": "unknown user",
    "bad_credentials": "invalid credentials",
    "inactive": "account inactive",
}
class UserService:
    def __init__(self, session: Session) -> None:
        self._session = session
    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.strip().lower())
        return self._session.scalar(stmt)
    def get_by_id(self, user_id: str) -> User | None:
        return self._session.get(User, user_id)
    def register(self, email: str, password: str) -> User:
        normalized = email.strip().lower()
        if self.get_by_email(normalized) is not None:
            raise EmailAlreadyRegisteredError(
                "An account with this email already exists."
            )
        user = User(
            id=uuid.uuid4().hex,
            email=normalized,
            hashed_password=hash_password(password),
            is_active=True,
        )
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        logger.info("User registered: user_id=%s", user.id)
        return user
    def authenticate(self, email: str, password: str) -> User | None:
        normalized = email.strip().lower()
        user = self.get_by_email(normalized)
        if user is None or not verify_password(password, user.hashed_password):
            reason = "unknown_user" if user is None else "bad_credentials"
            logger.warning(
                "Login failed: reason=%s (%s)",
                reason,
                _LOGIN_FAILURE_REASONS[reason],
            )
            return None
        if not user.is_active:
            logger.warning(
                "Login failed: reason=inactive (account inactive) user_id=%s",
                user.id,
            )
            return None
        logger.info("Login successful: user_id=%s", user.id)
        return user