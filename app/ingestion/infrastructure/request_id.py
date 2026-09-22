from __future__ import annotations
import uuid
from contextvars import ContextVar
_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
def generate_request_id() -> str:
    return str(uuid.uuid4())
def get_request_id() -> str:
    return _request_id_var.get()
def set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)
def bind_request_id(request_id: str | None = None) -> str:
    resolved = request_id or generate_request_id()
    _request_id_var.set(resolved)
    return resolved