from __future__ import annotations
import asyncio
import json
import re
from collections.abc import AsyncIterator
from starlette.requests import ClientDisconnect
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
    ChatResponseData,
    DocumentCitation,
)
if TYPE_CHECKING:
    from app.agents.coordinator import CoordinatorAgent
logger = get_logger(__name__)
_NOT_FOUND_MESSAGE = INSUFFICIENT_EVIDENCE_MESSAGE
_coordinator: CoordinatorAgent | None = None
def _get_coordinator(settings: Settings) -> CoordinatorAgent:
    global _coordinator
    if _coordinator is None:
        from app.agents.coordinator import CoordinatorAgent
        _coordinator = CoordinatorAgent(settings)
    return _coordinator
class ChatService:
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
        return self._store.purge_expired(self._settings.chat_retention_days)
    def list_sessions(
        self,
        owner_id: str | None,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        return self._store.list_sessions(owner_id, page=page, page_size=page_size)
    def list_messages(
        self,
        owner_id: str | None,
        session_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        return self._store.list_messages(owner_id, session_id, page=page, page_size=page_size)
    def delete_session(self, owner_id: str | None, session_id: str) -> bool:
        return self._store.delete_session(owner_id, session_id)
    def _restore_context(self, owner_id: str | None, session_id: str | None) -> None:
        if not session_id:
            return
        state = self._store.get_session_state(owner_id, session_id)
        if state:
            self._coordinator.hydrate_context(
                session_id,
                state.get("tickers") or [],
                state.get("query") or "",
                state.get("answer") or "",
                owner_id=owner_id,
            )
    @staticmethod
    def _owner_id(user: Any | None) -> str | None:
        return user.id if user is not None else None
    def _within_token_quota(self, owner_id: str | None, request: ChatRequest) -> bool:
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
        except Exception as exc:
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

        # Execution traces stay server-side. They are written to the log for
        # debugging and kept out of the stored message metadata, which the
        # messages endpoint hands back to the client.
        logger.debug(
            "chat turn trace query=%r plan=%s tools=%s",
            request.message[:120],
            list(result.plan or []),
            [item.get("tool") for item in result.tools_used],
        )

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
                "sources": list(result.sources or []),
                "answer": message,
            },
        )
        return ChatResponseData(
            message=message,
            ticker=result.tickers[0] if result.tickers else request.ticker,
            model=result.model,
            sources=_build_citations(result.sources, message),
        )
    async def stream_chat(
        self,
        request: ChatRequest,
        *,
        user: Any | None = None,
    ) -> AsyncIterator[str]:
        owner_id = self._owner_id(user)
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
        await asyncio.to_thread(
            self._restore_context,
            owner_id,
            request.session_id,
        )
        done_payload: dict[str, Any] | None = None

        stream = self._coordinator.stream_run(
            query=request.message,
            ticker=request.ticker,
            document_id=request.document_id,
            session_id=request.session_id,
            owner_id=owner_id,
        )
        try:
            async for event in stream:
                frame = dict(event)
                event_type = frame.pop("type", "message")
                if event_type == "done":
                    done_payload = frame
                    # Same citation filtering as the non-streaming path: offer
                    # only the pages the answer actually credits.
                    cited = _build_citations(
                        frame.get("sources") or [],
                        frame.get("message") or "",
                    )
                    frame["sources"] = [
                        citation.model_dump(mode="json") for citation in cited
                    ]
                yield _format_sse(event_type, frame)
        except ClientDisconnect:
            return
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(
                "Streaming chat failed for query %s: %s",
                request.message[:120],
                exc,
            )
            yield _format_sse("error", {"message": "The chat stream failed unexpectedly."})
            return
        finally:
            aclose = getattr(stream, "aclose", None)
            if aclose is not None:
                await aclose()
        if done_payload is not None:
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
                    "sources": list(done_payload.get("sources") or []),
                    "answer": done_payload.get("message", ""),
                },
            )
def _cited_pages(answer: str) -> set[tuple[str, int]] | None:
    """
    Pages the answer explicitly credits.

    The answer is required to end with ``Source: <filename>, p. <n>.`` lines, so
    those references are parsed back out and used to decide which retrieved
    pages are actually worth showing. Pages that were retrieved but never cited
    are not evidence for anything, and listing them made a one-page answer look
    like it was drawn from five.

    Returns ``None`` when nothing could be parsed, in which case the caller
    falls back to the top-scoring retrieved chunks rather than showing nothing.
    """
    if not answer:
        return None

    # A citation segment runs from one "Source" marker to the next, so a line
    # citing several files or pages is parsed as a unit rather than only the
    # first number being picked up.
    segments = re.split(r"\bsources?\s*:", answer, flags=re.IGNORECASE)[1:]

    cited: set[tuple[str, int]] = set()

    for segment in segments:
        # A single "Source:" line can credit several documents. Split on the
        # list separator first, otherwise the second document's page number is
        # attributed to the first document's title.
        for part in segment.split(";"):
            page_marker = re.search(
                r"\b(?:p{1,2}\.|pages?)\s*\d", part, flags=re.IGNORECASE
            )
            if page_marker is None:
                continue

            title = _normalise_title(part[: page_marker.start()])
            if not title:
                continue

            pages_part = part[page_marker.start() :]

            # Ranges first, so "pp. 3-5" contributes every page in between.
            for low, high in re.findall(r"(\d+)\s*[-–—]\s*(\d+)", pages_part):
                start, end = int(low), int(high)
                if 0 < start <= end <= 10_000:
                    cited.update((title, page) for page in range(start, end + 1))

            for number in re.findall(r"\d+", pages_part):
                value = int(number)
                if 0 < value <= 10_000:
                    cited.add((title, value))

    return cited or None


def _normalise_title(value: str) -> str:
    """
    Reduce a filename to a comparable form.

    Punctuation becomes a space first, so trailing marks left by the citation
    format ("...report.pdf, p. 3" leaves a comma) cannot defeat the extension
    strip. Without that, "Infosys AR.pdf," and "Infosys Annual Report.pdf"
    normalised differently and every citation was silently dropped.
    """
    spaced = re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip()
    without_extension = re.sub(r"\s(?:pdf|html?|txt|md)$", "", spaced)
    return without_extension.replace(" ", "")


def _build_citations(
    chunks: list[dict],
    answer: str = "",
) -> list[DocumentCitation]:
    """
    Grounding citations for the answer.

    When the answer names its sources, only those pages are returned so the UI
    never implies broader support than the response actually claims.
    """
    citations: list[DocumentCitation] = []
    seen: set[tuple[str, int | None]] = set()
    cited = _cited_pages(answer)

    for chunk in chunks:
        document_id = chunk.get("document_id")
        if not document_id:
            continue
        page = chunk.get("page")
        key = (document_id, page)
        if key in seen:
            continue

        if cited is not None:
            filename = _normalise_title(chunk.get("filename") or "")
            if page is None or (filename, int(page)) not in cited:
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
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
def _as_jsonable(value: Any) -> Any:
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
