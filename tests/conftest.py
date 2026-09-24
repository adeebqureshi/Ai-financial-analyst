import os
import tempfile
os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_TO_FILE", "false")
_default_auth_db = os.path.join(
    tempfile.gettempdir(),
    "ai-financial-analyst-test-auth.db",
).replace("\\", "/")
os.environ.setdefault("AUTH_DATABASE_URL", f"sqlite:///{_default_auth_db}")
_default_chat_db = os.path.join(
    tempfile.gettempdir(),
    "ai-financial-analyst-test-chat.db",
).replace("\\\\", "/")
os.environ.setdefault("CHAT_DATABASE_URL", f"sqlite:///{_default_chat_db}")

import pytest


@pytest.fixture(autouse=True)
def _reset_qdrant_singleton():
    yield
    try:
        from app.vectorstore.qdrant_store import _reset_shared_client_for_tests

        _reset_shared_client_for_tests()
    except Exception:
        pass