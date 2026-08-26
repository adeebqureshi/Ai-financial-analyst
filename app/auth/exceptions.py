"""
Authentication Exceptions

Domain exceptions raised by the authentication/authorization layer. They are
translated into structured ``APIResponse`` errors by the global exception
handlers registered in :mod:`app.api.exceptions`:

- ``AuthenticationError``  → HTTP 401 (missing/invalid credentials)
- ``AuthorizationError``   → HTTP 403 (authenticated but not allowed)
- ``EmailAlreadyRegisteredError`` → HTTP 409 (registration conflict)
"""

from __future__ import annotations


class AuthError(Exception):
    """Base class for all authentication/authorization errors."""

    error_code = "AUTH_000"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthenticationError(AuthError):
    """Raised when credentials are missing or invalid."""

    error_code = "AUTH_401"


class AuthorizationError(AuthError):
    """Raised when an authenticated user may not access a resource."""

    error_code = "AUTH_403"


class EmailAlreadyRegisteredError(AuthError):
    """Raised when registering an email address that already exists."""

    error_code = "AUTH_409"