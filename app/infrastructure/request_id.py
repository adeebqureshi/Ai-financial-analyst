"""
Request ID utilities.

Every HTTP request is assigned a correlation ID (UUID4) that is stored in a
``ContextVar`` so *any* code reachable from the request — services, agents,
LLM providers, ingestion jobs — can include it in its log records without
passing the ID through every function signature.

Design Decisions:
    - **ContextVar instead of parameter threading**: Keeps logging concerns
      out of business-logic signatures. Async-safe: each ``async`` task gets
      its own context copy.
    - **Incoming ``X-Request-ID`` honoured**: When a client (or upstream load
      balancer) supplies a request ID it is reused, enabling end-to-end
      tracing across services. Otherwise a new UUID4 is generated.
    - **Background jobs**: Long-lived worker code may call
      :func:`bind_request_id` with a job ID so its logs are equally
      correlatable.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def generate_request_id() -> str:
    """Return a fresh UUID4 request ID string."""
    return str(uuid.uuid4())


def get_request_id() -> str:
    """Return the request ID bound to the current context (``-`` if none)."""
    return _request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Bind ``request_id`` to the current context (used by the middleware)."""
    _request_id_var.set(request_id)


def bind_request_id(request_id: str | None = None) -> str:
    """
    Bind and return a request/job ID for the current context.

    Used by background jobs and startup tasks that run outside of the HTTP
    middleware. Passing ``None`` generates a fresh ID.
    """
    resolved = request_id or generate_request_id()
    _request_id_var.set(resolved)
    return resolved