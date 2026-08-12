"""
Async streaming pipeline tests.

Covers the coordinator's ``stream_run`` (event contract), the
``ChatService.stream_chat`` SSE framing, and the ``POST /chat/stream`` endpoint.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agents.audit_result import AuditResult
from app.agents.coordinator import CoordinatorAgent
from app.agents.intents import AgentIntent
from app.agents.research_plan import ResearchPlan
from app.api.dependencies.services import get_chat_service
from app.core.config import get_settings
from app.main import app
from app.schemas.analysis import ChatRequest
from app.services.chat_service import ChatService

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────────────
# CoordinatorAgent.stream_run
# ──────────────────────────────────────────────────────────────────────────


class _FakeAnalyst:
    """Minimal streaming analyst double for the coordinator."""

    def __init__(self, tokens: list[str], model: str = "fake-async-model") -> None:
        self._tokens = tokens
        self.provider = SimpleNamespace(MODEL=model)

    async def stream_synthesize(self, query, intents, evidence, sources, tickers):
        for token in self._tokens:
            yield token

    def ensure_async_client(self):
        return SimpleNamespace(provider=self.provider)


def _build_coordinator(
    tokens: list[str],
    *,
    audit_passed: bool = True,
    model: str = "fake-async-model",
) -> CoordinatorAgent:
    plan = ResearchPlan(
        query="What is Apple's price?",
        tickers=["AAPL"],
        intents=[AgentIntent.MARKET_DATA],
        tools=[],
        reasoning=["Retrieved market data for AAPL"],
    )

    coordinator = CoordinatorAgent()

    coordinator.planner = MagicMock()
    coordinator.planner.plan.return_value = plan

    coordinator._execute = MagicMock(
        return_value=(
            {
                "get_market_data": [
                    SimpleNamespace(status="done", result={"price": 220.0}, detail="ok")
                ]
            },
            ["Retrieved market data for AAPL"],
            [
                {
                    "tool": "get_market_data",
                    "status": "done",
                    "detail": "Retrieved market data for AAPL",
                }
            ],
            [],
        )
    )

    coordinator.analyst = _FakeAnalyst(tokens=tokens, model=model)

    coordinator.auditor = MagicMock()
    coordinator.auditor.audit_evidence.return_value = AuditResult(
        passed=audit_passed,
        issues=[] if audit_passed else ["unverified claim"],
    )

    return coordinator


@pytest.mark.anyio
async def test_stream_run_emits_plan_tokens_done():
    coordinator = _build_coordinator(["AAPL ", "is trading"])

    events = [event async for event in coordinator.stream_run(query="What is Apple's price?")]

    types = [event["type"] for event in events]

    assert types == ["plan", "token", "token", "done"]

    plan_event = events[0]
    assert plan_event["tickers"] == ["AAPL"]
    assert plan_event["steps"] == ["Retrieved market data for AAPL"]

    message = "".join(event["delta"] for event in events if event["type"] == "token")

    done_event = events[-1]
    assert done_event["type"] == "done"
    assert done_event["message"] == "AAPL is trading"
    assert done_event["model"] == "fake-async-model"
    assert done_event["success"] is True
    assert done_event["message"] == message


@pytest.mark.anyio
async def test_stream_run_appends_auditor_note_when_audit_fails():
    coordinator = _build_coordinator(["answer"], audit_passed=False)

    events = [event async for event in coordinator.stream_run(query="What is Apple's price?")]

    token_events = [event for event in events if event["type"] == "token"]

    # The auditor note is streamed as a final token delta.
    assert len(token_events) == 2
    assert "Auditor note" in token_events[-1]["delta"]

    done_event = events[-1]
    assert done_event["success"] is False
    assert done_event["message"].endswith(token_events[-1]["delta"])


@pytest.mark.anyio
async def test_stream_run_emits_error_when_planning_fails():
    coordinator = _build_coordinator(["x"])

    coordinator.planner.plan.side_effect = RuntimeError("boom")

    events = [event async for event in coordinator.stream_run(query="What is Apple's price?")]

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "Research failed" in events[0]["message"]


# ──────────────────────────────────────────────────────────────────────────
# ChatService.stream_chat (SSE framing)
# ──────────────────────────────────────────────────────────────────────────


class _FakeCoordinator:
    async def stream_run(self, query, ticker=None, document_id=None, session_id=None):
        yield {
            "type": "plan",
            "tickers": ["AAPL"],
            "intents": ["MARKET_DATA"],
            "steps": ["Ran tool"],
            "tools_used": [{"tool": "get_market_data", "status": "done", "detail": "Ran tool"}],
        }
        yield {"type": "token", "delta": "AAPL "}
        yield {"type": "token", "delta": "is trading"}
        yield {
            "type": "done",
            "message": "AAPL is trading",
            "model": "mock-llm",
            "success": True,
            "tickers": ["AAPL"],
            "intents": [],
            "sources": [],
            "steps": ["Ran tool"],
            "tools_used": [{"tool": "get_market_data", "status": "done", "detail": "Ran tool"}],
        }


@pytest.mark.anyio
async def test_stream_chat_formats_sse_frames():
    service = ChatService(get_settings(), coordinator=_FakeCoordinator())

    request = ChatRequest(message="What is Apple's price?", ticker="AAPL")

    frames = [frame async for frame in service.stream_chat(request)]

    assert len(frames) == 4

    assert frames[0].startswith("event: plan\n")
    assert "event: token\n" in frames[1]
    assert '"delta": "AAPL "' in frames[1]
    assert frames[-1].startswith("event: done\n")
    assert '"message": "AAPL is trading"' in frames[-1]


@pytest.mark.anyio
async def test_stream_chat_emits_error_frame_on_failure():
    class _BrokenCoordinator:
        async def stream_run(self, **kwargs):
            raise RuntimeError("boom")
            yield

    service = ChatService(get_settings(), coordinator=_BrokenCoordinator())

    frames = [frame async for frame in service.stream_chat(ChatRequest(message="hi"))]

    assert len(frames) == 1
    assert frames[0].startswith("event: error\n")
    assert "failed unexpectedly" in frames[0]


# ──────────────────────────────────────────────────────────────────────────
# POST /chat/stream endpoint
# ──────────────────────────────────────────────────────────────────────────


def test_chat_stream_endpoint_returns_sse():
    app.dependency_overrides[get_chat_service] = lambda: ChatService(
        get_settings(), coordinator=_FakeCoordinator()
    )

    try:
        response = client.post(
            "/chat/stream",
            json={"message": "What is Apple's price?", "ticker": "AAPL"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert "text/event-stream" in response.headers["content-type"]

    assert "event: plan\n" in response.text
    assert "event: token\n" in response.text
    assert "event: done\n" in response.text

    # Tokens progressively stream the answer; the done frame carries it whole.
    assert '"delta": "AAPL "' in response.text
    assert '"message": "AAPL is trading"' in response.text


def test_chat_stream_validates_request():
    response = client.post(
        "/chat/stream",
        json={"message": "price", "ticker": "TOO_LONG_TICKER"},
    )

    assert response.status_code == 422


def test_chat_stream_reconstructs_message_from_tokens():
    app.dependency_overrides[get_chat_service] = lambda: ChatService(
        get_settings(), coordinator=_FakeCoordinator()
    )

    try:
        response = client.post(
            "/chat/stream",
            json={"message": "What is Apple's price?", "ticker": "AAPL"},
        )
    finally:
        app.dependency_overrides.clear()

    tokens = []
    for frame in response.text.split("\n\n"):
        lines = frame.split("\n")
        event_type = ""
        payload = ""
        for line in lines:
            if line.startswith("event: "):
                event_type = line[len("event: ") :]
            elif line.startswith("data: "):
                payload = line[len("data: ") :]
        if event_type == "token":
            import json

            tokens.append(json.loads(payload)["delta"])

    assert "".join(tokens) == "AAPL is trading"
