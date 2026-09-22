from __future__ import annotations
class AuthError(Exception):
    error_code = "AUTH_000"
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
class AuthenticationError(AuthError):
    error_code = "AUTH_401"
class AuthorizationError(AuthError):
    error_code = "AUTH_403"
class EmailAlreadyRegisteredError(AuthError):
    error_code = "AUTH_409"