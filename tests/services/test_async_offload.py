import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.agents.coordinator import CoordinatorAgent
from app.agents.tools import ToolResult
from app.api.dependencies.services import get_chat_service
from app.api.routers import chat as chat_router
from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.schemas.analysis import ChatRequest
from app.schemas.responses import ChatResponseData
from app.services.chat_service import ChatService
class _BlockingTools:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._started = threading.Event()
        self.release = threading.Event()
        self.thread_id: int | None = None
    def execute(self, tool: str, args: dict, owner_id: str | None = None) -> ToolResult:
        self.thread_id = threading.get_ident()
        self._loop.call_soon_threadsafe(self._started.set)
        self.release.wait(timeout=5)
        return ToolResult(tool=tool, status="done", detail="ok", result={"value": 1})
class _FakeAnalyst:
    async def stream_synthesize(self, query, intents, evidence, sources, tickers):
        for token in ("answer ", "tokens"):
            yield token
class _FakeAuditor:
    def audit_evidence(self, plan, evidence, answer, sources, model):
        return SimpleNamespace(passed=True)
@pytest.mark.anyio
async def test_stream_run_offloads_blocking_tool_execution():
    tools = _BlockingTools(asyncio.get_running_loop())
    coordinator = CoordinatorAgent(
        get_settings(),
        tools=tools,
        analyst=_FakeAnalyst(),
        auditor=_FakeAuditor(),
    )
    loop_thread = threading.get_ident()
    probe_done = asyncio.Event()
    async def probe():
        await asyncio.sleep(0.05)
        probe_done.set()
    async def consume():
        async for _event in coordinator.stream_run("What is Apple's current price?"):
            pass
    stream_task = asyncio.create_task(consume())
    probe_task = asyncio.create_task(probe())
    await asyncio.wait_for(asyncio.to_thread(tools._started.wait), timeout=2)
    await asyncio.wait_for(probe_done.wait(), timeout=1)
    probe_task.cancel()
    tools.release.set()
    await asyncio.wait_for(stream_task, timeout=5)
    assert tools.thread_id is not None
    assert tools.thread_id != loop_thread
@pytest.mark.anyio
async def test_stream_chat_preserves_sse_contract_and_persists():
    coordinator = MagicMock()
    async def stream_run(**kwargs):
        yield {
            "type": "plan",
            "tickers": ["AAPL"],
            "intents": ["MARKET_DATA"],
            "steps": ["Retrieved market data for AAPL"],
            "tools_used": [],
        }
        yield {"type": "token", "delta": "AAPL is trading"}
        yield {
            "type": "done",
            "message": "AAPL is trading at $220.10.",
            "model": "fake",
            "success": True,
            "tickers": ["AAPL"],
            "intents": ["MARKET_DATA"],
            "sources": [],
            "steps": ["Retrieved market data for AAPL"],
            "tools_used": [],
        }
    coordinator.stream_run = stream_run
    store = MagicMock()
    service = ChatService(get_settings(), coordinator=coordinator, store=store)
    frames = [
        frame
        async for frame in service.stream_chat(
            ChatRequest(message="What is Apple's price?", session_id="s1")
        )
    ]
    assert frames[0].startswith("event: plan\n")
    assert any(frame.startswith("event: token\n") for frame in frames)
    assert any(frame.startswith("event: done\n") for frame in frames)
    assert '"message": "AAPL is trading at $220.10."' in frames[-1]
    store.save_turn.assert_called_once()
def test_chat_route_preserves_response_contract_with_offloaded_service():
    app = FastAPI()
    app.include_router(chat_router.router)
    mock_service = MagicMock()
    mock_service.chat.return_value = ChatResponseData(
        message="AAPL is trading at $220.10.",
        ticker="AAPL",
        model="fake",
        sources=[],
        plan=["Retrieved market data for AAPL"],
        tools_used=[],
    )
    app.dependency_overrides[get_chat_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: None
    client = TestClient(app)
    response = client.post("/chat", json={"message": "What is Apple's price?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["message"] == "AAPL is trading at $220.10."
    mock_service.chat.assert_called_once()