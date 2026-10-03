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

# Load embedding/reranker weights from the local Hugging Face cache only. Without
# this, `huggingface_hub` performs a HEAD request to check for model updates even
# when the weights are already cached, so the suite depends on the network for
# tests that are otherwise hermetic.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import pytest

# Hosts the test suite is allowed to reach. Everything else is refused so that
# an accidental live provider call fails fast and loudly instead of blocking on
# DNS/retries until pytest-timeout kills the run.
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost", "0.0.0.0", ""}


def _is_external(address) -> bool:
    if isinstance(address, tuple) and address:
        host = address[0]
        return str(host) not in _LOOPBACK_HOSTS
    return False


@pytest.fixture(autouse=True)
def _block_external_network(request):
    """Refuse outbound connections to real external services during unit tests.

    The suite already pins ``LLM_PROVIDER=mock`` and an in-memory Qdrant, but
    the SEC EDGAR, Yahoo Finance and FMP clients are reachable from tests that
    build agents from ambient settings. A previous full-suite run hung at ~82%
    on ``edgar`` → ``tenacity`` → ``time.sleep`` after Yahoo/FMP failed with
    DNS errors.

    Blocking the socket keeps the default suite deterministic and offline. Tests
    that genuinely need a provider opt out with ``@pytest.mark.integration``,
    which already exists in pyproject.toml for real external services.
    """
    if request.node.get_closest_marker("integration"):
        yield
        return

    import socket

    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def guarded_connect(self, address):
        if _is_external(address):
            raise ConnectionError(
                f"Blocked external network call to {address!r} during tests. "
                "Mark the test with @pytest.mark.integration if it genuinely "
                "requires an external service."
            )
        return real_connect(self, address)

    def guarded_connect_ex(self, address):
        if _is_external(address):
            raise ConnectionError(
                f"Blocked external network call to {address!r} during tests."
            )
        return real_connect_ex(self, address)

    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = guarded_connect_ex
    try:
        yield
    finally:
        socket.socket.connect = real_connect
        socket.socket.connect_ex = real_connect_ex


@pytest.fixture(autouse=True)
def _reset_qdrant_singleton():
    yield
    try:
        from app.vectorstore.qdrant_store import _reset_shared_client_for_tests

        _reset_shared_client_for_tests()
    except Exception:
        pass
