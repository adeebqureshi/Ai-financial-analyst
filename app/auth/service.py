"""
User Service

Account registration and credential verification backed by the
authentication database.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.exceptions import EmailAlreadyRegisteredError
from app.auth.models import User
from app.auth.security import hash_password, verify_password


class UserService:
    """Account management operations for :class:`~app.auth.models.User`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> User | None:
        """Return the user with the given email (case-insensitive)."""
        stmt = select(User).where(User.email == email.strip().lower())

        return self._session.scalar(stmt)

    def get_by_id(self, user_id: str) -> User | None:
        """Return the user with the given id, if any."""
        return self._session.get(User, user_id)

    def register(self, email: str, password: str) -> User:
        """
        Create a new account.

        Args:
            email: The login email address.
            password: The plaintext password (hashed before storage).

        Returns:
            The persisted ``User``.

        Raises:
            EmailAlreadyRegisteredError: When the email is already in use.
        """
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

        return user

    def authenticate(self, email: str, password: str) -> User | None:
        """
        Verify credentials.

        Returns:
            The matching active ``User``, or ``None`` when the credentials
            are wrong or the account is inactive.
        """
        normalized = email.strip().lower()

        user = self.get_by_email(normalized)

        if user is None or not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user