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
os.environ.setdefault("QDRANT_URL", "")

# The test suite must never reach a real LLM endpoint. Several tests build a
# CoordinatorAgent from ambient settings, which previously constructed a live
# OpenAI-compatible client and blocked on a real HTTP call. Forcing the mock
# provider keeps the suite hermetic and fast; tests that exercise a specific
# provider inject it explicitly instead of relying on the environment.
os.environ["LLM_PROVIDER"] = "mock"
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("FREELLMAPI_API_KEY", None)

# Keep model-dependent components off the network during tests.
os.environ.setdefault("ENABLE_RERANKER", "false")
os.environ.setdefault("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

import pytest


@pytest.fixture(autouse=True)
def _reset_qdrant_singleton():
    yield
    try:
        from app.vectorstore.qdrant_store import _reset_shared_client_for_tests

        _reset_shared_client_for_tests()
    except Exception:
        pass
