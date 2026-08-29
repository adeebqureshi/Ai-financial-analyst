"""
Chat Router

This module defines the conversational AI endpoints:

- ``POST /chat``                  — non-streaming chat response.
- ``POST /chat/stream``           — Server-Sent Events (SSE) streaming chat response.
- ``GET /chat/sessions``          — list the caller's persisted sessions (paginated).
- ``GET /chat/sessions/{id}/messages`` — list a session's messages (paginated).
- ``DELETE /chat/sessions/{id}``  — delete a session (ownership-scoped).

Design Decisions:
    - **No business logic in route**: Route handlers delegate entirely to
      ``ChatService``.
    - **Dependency injection**: ``ChatService`` is injected via
      ``Depends(get_chat_service)``, making it overridable in tests.
    - **Ownership isolation**: The authenticated ``User`` (``None`` when auth
      is disabled) scopes both persistence and every read/delete — a caller
      can only ever see or mutate their own sessions.
    - **Standard response format**: Returns ``APIResponse[T]``.
    - **SSE for streaming**: ``/chat/stream`` returns a ``StreamingResponse``
      with ``text/event-stream``; each SSE frame is self-contained so a client
      can render tokens as they arrive.
    - **Rate limiting**: Chat endpoints are rate limited per user/IP.
"""

from __future__ import annotations

import asyncio
import math

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import rate_limit_chat
from app.api.dependencies.services import get_chat_service
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.schemas.analysis import ChatRequest
from app.schemas.base import APIResponse, PaginationMeta
from app.schemas.responses import (
    ChatMessageData,
    ChatMessageListData,
    ChatResponseData,
    ChatSessionData,
    ChatSessionListData,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


def _owner_id(current_user: User | None) -> str | None:
    """Return the owner id for the caller (None when auth is disabled)."""
    return current_user.id if current_user is not None else None


@router.post(
    "",
    response_model=APIResponse[ChatResponseData],
    summary="Chat with the AI analyst",
    description="Sends a message to the LLM-powered financial analyst and returns a response.",
    dependencies=[Depends(rate_limit_chat)],
)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[ChatResponseData]:
    """
    Chat endpoint.

    Args:
        request: The validated chat request.
        service: Injected ``ChatService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        An ``APIResponse`` containing the assistant reply.
    """
    result = await asyncio.to_thread(service.chat, request, user=current_user)

    return APIResponse.success_response(
        message="Chat response generated",
        data=result,
    )


@router.post(
    "/stream",
    summary="Stream a chat response",
    description=(
        "Sends a message to the LLM-powered financial analyst and streams the "
        "answer back as Server-Sent Events (SSE). Emits ``plan``, ``token``, "
        "``done`` and ``error`` events so clients can render tokens live."
    ),
    dependencies=[Depends(rate_limit_chat)],
)
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
    current_user: User | None = Depends(get_current_user),
) -> StreamingResponse:
    """
    Streaming chat endpoint.

    Args:
        request: The validated chat request.
        service: Injected ``ChatService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        A ``StreamingResponse`` emitting SSE frames as tokens are generated.
    """
    return StreamingResponse(
        service.stream_chat(request, user=current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/sessions",
    response_model=APIResponse[ChatSessionListData],
    summary="List persisted chat sessions",
    description="Returns the caller's persisted sessions, newest-first.",
    dependencies=[Depends(rate_limit_chat)],
)
async def list_sessions(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page."),
    service: ChatService = Depends(get_chat_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[ChatSessionListData]:
    """
    List the caller's chat sessions.

    Args:
        page: Page number (1-indexed).
        page_size: Items per page.
        service: Injected ``ChatService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        An ``APIResponse`` with a paginated list of the caller's sessions.
    """
    sessions, total = await asyncio.to_thread(
        service.list_sessions,
        _owner_id(current_user),
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total / page_size)

    return APIResponse.success_response(
        message=f"{total} chat sessions",
        data=ChatSessionListData(
            sessions=[ChatSessionData(**session) for session in sessions],
            total=total,
        ),
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=APIResponse[ChatMessageListData],
    summary="List a session's messages",
    description="Returns the caller's messages for one session, oldest-first.",
    dependencies=[Depends(rate_limit_chat)],
)
async def list_messages(
    session_id: str,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page."),
    service: ChatService = Depends(get_chat_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[ChatMessageListData]:
    """
    List messages in an owned session.

    Args:
        session_id: The session identifier.
        page: Page number (1-indexed).
        page_size: Items per page.
        service: Injected ``ChatService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        An ``APIResponse`` with a paginated list of the session's messages.
    """
    messages, total = await asyncio.to_thread(
        service.list_messages,
        _owner_id(current_user),
        session_id,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total / page_size)

    return APIResponse.success_response(
        message=f"{total} messages in session",
        data=ChatMessageListData(
            messages=[ChatMessageData(**message) for message in messages],
            total=total,
        ),
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=APIResponse[dict],
    summary="Delete a chat session",
    description="Deletes one of the caller's sessions and all its messages.",
    dependencies=[Depends(rate_limit_chat)],
)
async def delete_session(
    session_id: str,
    service: ChatService = Depends(get_chat_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[dict]:
    """
    Delete an owned session.

    Args:
        session_id: The session identifier.
        service: Injected ``ChatService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        An ``APIResponse`` confirming whether the session was deleted.
    """
    deleted = await asyncio.to_thread(
        service.delete_session,
        _owner_id(current_user),
        session_id,
    )

    return APIResponse.success_response(
        message="Session deleted" if deleted else "Session not found",
        data={"deleted": deleted, "session_id": session_id},
    )