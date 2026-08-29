"""
Pytest Configuration

Sets the process environment BEFORE any application module is imported so
the test suite runs with authentication disabled. This preserves the exact
pre-existing API behaviour for legacy endpoint tests; dedicated integration
tests in ``tests/auth`` explicitly enable auth and exercise the full
register/login/401/403 flows.
"""

import os
import tempfile

os.environ.setdefault("AUTH_ENABLED", "false")

# Keep the auth SQLite store out of the repository working tree even when a
# request resolves the (disabled) database dependency.
_default_auth_db = os.path.join(
    tempfile.gettempdir(),
    "ai-financial-analyst-test-auth.db",
).replace("\\", "/")
os.environ.setdefault("AUTH_DATABASE_URL", f"sqlite:///{_default_auth_db}")

# Keep the chat conversation store out of the repository working tree. The
# chat service now persists each turn by default, so tests must not write to
# ``./data/chat.db`` inside the repository.
_default_chat_db = os.path.join(
    tempfile.gettempdir(),
    "ai-financial-analyst-test-chat.db",
).replace("\\\\", "/")
os.environ.setdefault("CHAT_DATABASE_URL", f"sqlite:///{_default_chat_db}")