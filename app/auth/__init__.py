"""
Authentication & Authorization Package

Production-ready account authentication for the FastAPI backend:

- PBKDF2-HMAC-SHA256 password hashing (standard library, no native deps).
- Signed HS256 JWT bearer access tokens (``PyJWT``).
- SQLAlchemy-backed user accounts (SQLite by default, Postgres-ready).
- ``get_current_user`` / ``require_authenticated_user`` dependencies that
  guard business routers and supply identities for ownership checks.

This package intentionally performs no eager imports: ``app.auth.dependencies``
is imported by API routers during application assembly, so pulling it in here
would create an import cycle (``app.api`` -> routers -> ``app.auth``).
Import from the concrete submodules instead::

    from app.auth.dependencies import get_current_user
    from app.auth.exceptions import AuthenticationError
"""