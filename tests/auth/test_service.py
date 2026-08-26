"""
Unit tests for the user account service (:mod:`app.auth.service`).
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import sessionmaker

from app.auth.database import Base, get_engine, init_db
from app.auth.exceptions import EmailAlreadyRegisteredError
from app.auth.models import User
from app.auth.service import UserService
from app.core.config import Settings


@pytest.fixture()
def session(tmp_path):
    """A real SQLite-backed session isolated to a temp directory."""
    settings = Settings(
        auth_database_url=f"sqlite:///{tmp_path / 'auth.db'}",
    )

    init_db(settings)

    factory = sessionmaker(bind=get_engine(settings), expire_on_commit=False)

    s = factory()

    yield s

    s.close()

    # Drop tables so each test starts from an empty store.
    Base.metadata.drop_all(bind=get_engine(settings))


class TestRegister:
    def test_register_creates_active_user(self, session):
        user = UserService(session).register("Analyst@Example.com ", "password123")

        assert user.id
        assert user.email == "analyst@example.com"  # normalised
        assert user.is_active is True
        assert user.hashed_password != "password123"

    def test_duplicate_email_is_rejected(self, session):
        service = UserService(session)

        service.register("dupe@example.com", "password123")

        with pytest.raises(EmailAlreadyRegisteredError):
            service.register("dupe@example.com", "other-password")

    def test_email_lookup_is_case_insensitive(self, session):
        UserService(session).register("mixed@Example.COM", "password123")

        found = UserService(session).get_by_email("MIXED@example.com")

        assert found is not None


class TestAuthenticate:
    def test_valid_credentials_return_user(self, session):
        UserService(session).register("login@example.com", "password123")

        user = UserService(session).authenticate("login@example.com", "password123")

        assert user is not None

    def test_wrong_password_returns_none(self, session):
        UserService(session).register("login@example.com", "password123")

        assert (
            UserService(session).authenticate("login@example.com", "wrong-pass")
            is None
        )

    def test_unknown_user_returns_none(self, session):
        assert (
            UserService(session).authenticate("ghost@example.com", "whatever")
            is None
        )

    def test_inactive_user_cannot_authenticate(self, session):
        service = UserService(session)

        user = service.register("inactive@example.com", "password123")

        user.is_active = False
        session.commit()

        assert (
            service.authenticate("inactive@example.com", "password123") is None
        )

    def test_stored_password_is_hashed(self, session):
        user = UserService(session).register("hashed@example.com", "plaintext-pw")

        stored = session.get(User, user.id).hashed_password

        assert stored != "plaintext-pw"
        assert "pbkdf2_sha256" in stored