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

import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from app.agents.financial_analyst import INSUFFICIENT_EVIDENCE_MESSAGE
from app.core.config import Settings
from app.core.logging import get_logger
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
    """

    def __init__(
        self,
        settings: Settings,
        coordinator: CoordinatorAgent | None = None,
    ) -> None:
        self._settings = settings

        if coordinator is None:
            coordinator = _get_coordinator(settings)

        self._coordinator = coordinator

    def chat(self, request: ChatRequest) -> ChatResponseData:
        """
        Send a chat message and get an evidence-grounded AI response.

        Args:
            request: The validated chat request.

        Returns:
            A ``ChatResponseData`` with the assistant reply, sources and the
            tools that actually ran.
        """
        result = self._coordinator.run(
            query=request.message,
            ticker=request.ticker,
            document_id=request.document_id,
            session_id=request.session_id,
        )

        return ChatResponseData(
            message=result.message or result.report.body,
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

    async def stream_chat(self, request: ChatRequest) -> AsyncIterator[str]:
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

        Yields:
            SSE-formatted frames for the streaming ``POST /chat/stream`` route.
        """
        try:
            async for event in self._coordinator.stream_run(
                query=request.message,
                ticker=request.ticker,
                document_id=request.document_id,
                session_id=request.session_id,
            ):
                frame = dict(event)
                event_type = frame.pop("type", "message")
                yield _format_sse(event_type, frame)
        except Exception as exc:
            logger.warning(
                "Streaming chat failed for query %s: %s",
                request.message[:120],
                exc,
            )
            yield _format_sse("error", {"message": "The chat stream failed unexpectedly."})


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
