"""
Chat Service

This module contains the business logic for the conversational AI chat
endpoint. It delegates to the agentic pipeline (``CoordinatorAgent``) which:

    1. classifies the question intent,
    2. selects the minimal set of existing tools,
    3. executes them (market data, financials, valuation, health, risk,
       comparison, RAG retrieval, ...),
    4. synthesizes an evidence-grounded answer,
    5. audits it for fabrication / ticker isolation,
    6. returns the answer together with real sources and the tools that ran.

The endpoint's request contract (``message`` / ``ticker`` / ``document_id`` /
``context``) and response model are preserved; ``plan`` and ``tools_used`` are
added backward-compatibly for tool transparency.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from app.agents.financial_analyst import INSUFFICIENT_EVIDENCE_MESSAGE
from app.chat.cache import ChatSessionCache
from app.chat.store import ChatStore
from app.core.config import Settings
from app.core.exceptions import QuotaExceededError
from app.core.logging import get_logger
from app.llm.quota import get_token_quota
from app.llm.tokenizer import Tokenizer
from app.schemas.analysis import ChatRequest
from app.schemas.responses import (
    AgentToolExecutionData,
    ChatResponseData,
    DocumentCitation,
)

if TYPE_CHECKING:
    from app.agents.coordinator import CoordinatorAgent

logger = get_logger(__name__)

# Kept as an alias for callers / tests that referenced the previous constant.
_NOT_FOUND_MESSAGE = INSUFFICIENT_EVIDENCE_MESSAGE

# Process-wide coordinator shared by every ``ChatService``. The coordinator
# owns ``ConversationMemory`` which is keyed by ``session_id`` and therefore
# must outlive individual HTTP requests — a per-request coordinator would
# forget every session and multi-turn follow-ups ("what about its valuation?")
# would never resolve. The coordinator and its underlying services are
# otherwise stateless per run, so a single shared instance is safe.
_coordinator: CoordinatorAgent | None = None


def _get_coordinator(settings: Settings) -> CoordinatorAgent:
    """
    Return the process-wide coordinator, building it once on first use.
    """
    global _coordinator

    if _coordinator is None:
        # Imported lazily to avoid a module-level import cycle between
        # app.agents.coordinator -> tools -> services -> chat_service.
        from app.agents.coordinator import CoordinatorAgent

        _coordinator = CoordinatorAgent(settings)

    return _coordinator


class ChatService:
    """
    Service for conversational AI chat grounded in the agentic pipeline.

    Every turn is also persisted to the chat store (PostgreSQL in production,
    SQLite in development) so conversations survive restarts and are shared
    across workers/containers. Persistence is ownership-scoped and is a
    best-effort side effect — it never alters or interrupts the response
    contract.
    """

    def __init__(
        self,
        settings: Settings,
        coordinator: CoordinatorAgent | None = None,
        store: ChatStore | None = None,
    ) -> None:
        self._settings = settings

        if coordinator is None:
            coordinator = _get_coordinator(settings)

        self._coordinator = coordinator

        if store is None:
            cache = ChatSessionCache(settings.chat_redis_url)
            store = ChatStore(
                settings.chat_database_url,
                cache=cache,
                retention_days=settings.chat_retention_days,
            )

        self._store = store

    def cleanup_expired_sessions(self) -> int:
        """
        Purge sessions idle longer than the configured retention window.

        Returns:
            The number of sessions removed.
        """
        return self._store.purge_expired(self._settings.chat_retention_days)

    def list_sessions(
        self,
        owner_id: str | None,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return the caller's sessions (newest-first) and the total count."""
        return self._store.list_sessions(owner_id, page=page, page_size=page_size)

    def list_messages(
        self,
        owner_id: str | None,
        session_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return an owned session's messages (oldest-first) and the total."""
        return self._store.list_messages(owner_id, session_id, page=page, page_size=page_size)

    def delete_session(self, owner_id: str | None, session_id: str) -> bool:
        """Delete an owned session (and its messages). Returns False if absent."""
        return self._store.delete_session(owner_id, session_id)

    def _restore_context(self, owner_id: str | None, session_id: str | None) -> None:
        """Replay persisted session state into the coordinator's memory."""
        if not session_id:
            return

        state = self._store.get_session_state(owner_id, session_id)

        if state:
            self._coordinator.hydrate_context(
                session_id,
                state.get("tickers") or [],
                state.get("query") or "",
                state.get("answer") or "",
            )

    @staticmethod
    def _owner_id(user: Any | None) -> str | None:
        """Return the owner id for the caller (None when auth is disabled)."""
        return user.id if user is not None else None

    def _within_token_quota(self, owner_id: str | None, request: ChatRequest) -> bool:
        """
        Charge this turn's estimated token cost against the caller's daily
        LLM budget.

        The estimate is the prompt size plus the configured output reserve
        (``llm_max_tokens``) — deliberately conservative, since actual
        provider usage is not known before the call. Returns ``False`` when
        the budget is exhausted. Unauthenticated calls (no ``owner_id``) and
        disabled quotas always pass.
        """
        if owner_id is None:
            return True

        quota = get_token_quota(self._settings)

        if not quota.enabled:
            return True

        estimated = Tokenizer.count(request.message) + self._settings.llm_max_tokens

        return quota.consume(owner_id, estimated)

    def _persist_turn(
        self,
        owner_id: str | None,
        request: ChatRequest,
        *,
        message: str,
        assistant_meta: dict[str, Any],
    ) -> None:
        """
        Best-effort, non-fatal persistence of a completed turn.

        Persistence failures are logged and swallowed so chat availability and
        the response contract are never affected by storage outages.
        """
        if not request.session_id:
            return

        try:
            self._store.save_turn(
                owner_id,
                request.session_id,
                user_message=request.message,
                assistant_message=message,
                user_meta=_as_jsonable(
                    {
                        "role": "user",
                        "ticker": request.ticker,
                        "document_id": request.document_id,
                        "context": request.context,
                        "as_of_date": str(request.as_of_date) if request.as_of_date else None,
                    }
                ),
                assistant_meta=_as_jsonable(assistant_meta),
            )
        except Exception as exc:  # pragma: no cover - defensive best-effort
            logger.warning(
                "Failed to persist chat turn for session %s: %s",
                request.session_id,
                exc,
            )

    def chat(
        self,
        request: ChatRequest,
        *,
        user: Any | None = None,
    ) -> ChatResponseData:
        """
        Send a chat message and get an evidence-grounded AI response.

        The authenticated ``user`` (when auth is enabled) scopes persistence so
        the conversation is recorded under that user's ownership.

        Args:
            request: The validated chat request.
            user: The authenticated user (or ``None`` when auth is disabled).

        Returns:
            A ``ChatResponseData`` with the assistant reply, sources and the
            tools that actually ran.
        """
        owner_id = self._owner_id(user)

        if not self._within_token_quota(owner_id, request):
            raise QuotaExceededError(
                "Daily LLM token quota exceeded. Please try again tomorrow "
                "or contact your administrator.",
                error_code="QUOTA_EXCEEDED",
            )

        self._restore_context(owner_id, request.session_id)

        result = self._coordinator.run(
            query=request.message,
            ticker=request.ticker,
            document_id=request.document_id,
            session_id=request.session_id,
            owner_id=owner_id,
        )

        message = result.message or result.report.body

        self._persist_turn(
            owner_id,
            request,
            message=message,
            assistant_meta={
                "role": "assistant",
                "query": request.message,
                "tickers": list(result.tickers or []),
                "model": result.model,
                "intents": list(result.intents or []),
                "success": bool(result.success),
                "ticker": request.ticker,
                "document_id": request.document_id,
                "plan": list(result.plan or []),
                "tools_used": [
                    {
                        "tool": item.get("tool", ""),
                        "status": item.get("status", "done"),
                        "detail": item.get("detail"),
                    }
                    for item in result.tools_used
                ],
                "sources": list(result.sources or []),
                "answer": message,
            },
        )

        return ChatResponseData(
            message=message,
            ticker=result.tickers[0] if result.tickers else request.ticker,
            model=result.model,
            sources=_build_citations(result.sources),
            plan=result.plan,
            tools_used=[
                AgentToolExecutionData(
                    tool=item.get("tool", ""),
                    status=item.get("status", "done"),
                    detail=item.get("detail"),
                )
                for item in result.tools_used
            ],
        )

    async def stream_chat(
        self,
        request: ChatRequest,
        *,
        user: Any | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream an evidence-grounded AI response as Server-Sent Events.

        Each yielded string is a complete SSE frame of the form::

            event: <type>
            data: <json>

        Event types:
            - ``plan``  — planning / tool metadata (steps, tools_used, tickers).
            - ``token`` — a progressive text delta of the answer.
            - ``done``  — the final result (message, model, sources, ...).
            - ``error`` — a clean failure frame (never a raw exception).

        Args:
            request: The validated chat request.
            user: The authenticated user (or ``None`` when auth is disabled).

        Yields:
            SSE-formatted frames for the streaming ``POST /chat/stream`` route.
        """
        owner_id = self._owner_id(user)

        # Quota enforcement happens before any SSE frame is emitted so an
        # exhausted budget is a clean, first-frame failure — never a stream
        # that dies halfway through.
        if not self._within_token_quota(owner_id, request):
            yield _format_sse(
                "error",
                {
                    "message": (
                        "Daily LLM token quota exceeded. Please try again "
                        "tomorrow or contact your administrator."
                    ),
                    "code": "QUOTA_EXCEEDED",
                },
            )
            return

        # Session-state replay hits the chat database synchronously; offload it
        # so the SSE stream never blocks the event loop while restoring.
        await asyncio.to_thread(
            self._restore_context,
            owner_id,
            request.session_id,
        )

        done_payload: dict[str, Any] | None = None

        try:
            async for event in self._coordinator.stream_run(
                query=request.message,
                ticker=request.ticker,
                document_id=request.document_id,
                session_id=request.session_id,
                owner_id=owner_id,
            ):
                frame = dict(event)
                event_type = frame.pop("type", "message")

                if event_type == "done":
                    done_payload = frame

                yield _format_sse(event_type, frame)
        except Exception as exc:
            logger.warning(
                "Streaming chat failed for query %s: %s",
                request.message[:120],
                exc,
            )
            yield _format_sse("error", {"message": "The chat stream failed unexpectedly."})
            return

        if done_payload is not None:
            # Turn persistence performs synchronous database I/O; offload it so
            # finishing the stream never blocks the event loop.
            await asyncio.to_thread(
                self._persist_turn,
                owner_id,
                request,
                message=done_payload.get("message", ""),
                assistant_meta={
                    "role": "assistant",
                    "query": request.message,
                    "tickers": list(done_payload.get("tickers") or []),
                    "model": done_payload.get("model"),
                    "intents": list(done_payload.get("intents") or []),
                    "success": bool(done_payload.get("success", True)),
                    "ticker": request.ticker,
                    "document_id": request.document_id,
                    "plan": list(done_payload.get("steps") or []),
                    "tools_used": list(done_payload.get("tools_used") or []),
                    "sources": list(done_payload.get("sources") or []),
                    "answer": done_payload.get("message", ""),
                },
            )


def _build_citations(chunks: list[dict]) -> list[DocumentCitation]:
    """
    Convert retrieved chunks into stable source citations.

    Only chunks with a document id are cited — the answer can never reference
    a source that was not actually retrieved.
    """
    citations: list[DocumentCitation] = []

    seen: set[tuple[str, int | None]] = set()

    for chunk in chunks:
        document_id = chunk.get("document_id")

        if not document_id:
            continue

        page = chunk.get("page")

        key = (document_id, page)

        if key in seen:
            continue

        seen.add(key)

        citations.append(
            DocumentCitation(
                document_id=document_id,
                filename=chunk.get("filename") or "Unknown document",
                page=page,
                chunk_id=chunk.get("chunk_id"),
                score=chunk.get("score"),
            )
        )

    return citations


def _format_sse(event: str, data: dict) -> str:
    """
    Serialize a chat event into a Server-Sent Events frame.

    Args:
        event: The SSE event type (``plan`` / ``token`` / ``done`` / ``error``).
        data: Serializable event payload.

    Returns:
        A single SSE frame terminated by a blank line.
    """
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def _as_jsonable(value: Any) -> Any:
    """
    Recursively coerce ``value`` into a purely JSON-serializable structure.

    Pydantic models are dumped to dicts; anything else unrecognized (datetimes,
    numpy scalars, custom objects, ...) is stringified so persistence metadata
    can always be stored in a JSON column without raising.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {_as_jsonable(k): _as_jsonable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_as_jsonable(item) for item in value]

    if isinstance(value, set):
        return [_as_jsonable(item) for item in value]

    if hasattr(value, "model_dump"):
        return _as_jsonable(value.model_dump())

    return str(value)
