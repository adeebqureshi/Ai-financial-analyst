"""
LLM reliability and cost-control tests.

Covers:
    - ``RetryPolicy.execute_async`` (transient retry, non-retryable pass-through)
    - ``AsyncOpenAIProvider.generate`` retry with exponential backoff
    - ``AsyncOpenAIProvider.stream`` typed-error mapping on mid-stream failure
    - ``TokenQuotaEnforcer`` accounting
    - ``ChatService`` per-user token quota enforcement (sync + streaming)
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import openai
import pytest

from app.core.exceptions import QuotaExceededError
from app.llm.exceptions import ProviderError
from app.llm.exceptions import RateLimitError
from app.llm.exceptions import TimeoutError
from app.llm.models import LLMRequest
from app.llm.providers.async_openai_provider import AsyncOpenAIProvider
from app.llm.quota import TokenQuotaEnforcer, reset_token_quota
from app.llm.retry import RetryPolicy
from app.schemas.analysis import ChatRequest
from app.services import chat_service as chat_service_module
from app.services.chat_service import ChatService


# ──────────────────────────────────────────────────────────────────────────────
# RetryPolicy.execute_async
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_async_retries_transient_then_succeeds():
    policy = RetryPolicy(max_attempts=3, base_delay=0)

    calls = 0

    async def flaky():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TimeoutError("timed out")
        return "ok"

    assert await policy.execute_async(flaky) == "ok"
    assert calls == 3


@pytest.mark.asyncio
async def test_execute_async_exhausts_rate_limit_retries():
    policy = RetryPolicy(max_attempts=2, base_delay=0)

    async def always_limited():
        raise RateLimitError("429")

    with pytest.raises(RateLimitError):
        await policy.execute_async(always_limited)


@pytest.mark.asyncio
async def test_execute_async_does_not_retry_provider_errors():
    policy = RetryPolicy(max_attempts=3, base_delay=0)

    calls = 0

    async def bad_key():
        nonlocal calls
        calls += 1
        raise ProviderError("auth failed")

    with pytest.raises(ProviderError):
        await policy.execute_async(bad_key)

    assert calls == 1


# ──────────────────────────────────────────────────────────────────────────────
# AsyncOpenAIProvider — retry + mid-stream error mapping
# ──────────────────────────────────────────────────────────────────────────────


class _FakeAsyncStream:
    """Async iterator over chunks that can raise mid-iteration."""

    def __init__(self, chunks_and_errors: list) -> None:
        self._items = list(chunks_and_errors)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._items:
            raise StopAsyncIteration
        item = self._items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _chunk(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=content))]
    )


def _provider_with_client(create_mock: AsyncMock, retry: RetryPolicy | None = None):
    provider = AsyncOpenAIProvider(
        config=SimpleNamespace(
            model="gpt-test", temperature=0.0, max_tokens=16, timeout=5
        ),
        api_key="sk-test",
        retry_policy=retry or RetryPolicy(max_attempts=1, base_delay=0),
    )
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create_mock)
        )
    )
    return provider


@pytest.mark.asyncio
async def test_generate_retries_transient_failures():
    good = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="hi"))],
        model="gpt-test",
    )
    create_mock = AsyncMock(side_effect=[TimeoutError("t"), good])

    provider = _provider_with_client(
        create_mock, RetryPolicy(max_attempts=2, base_delay=0)
    )

    response = await provider.generate(LLMRequest(prompt="hello"))

    assert response.text == "hi"
    assert create_mock.await_count == 2


@pytest.mark.asyncio
async def test_stream_maps_mid_stream_failure_to_typed_error():
    connection_error = openai.APIConnectionError(request=SimpleNamespace())
    create_mock = AsyncMock(
        return_value=_FakeAsyncStream([_chunk("partial"), connection_error])
    )

    provider = _provider_with_client(create_mock)

    received: list[str] = []

    with pytest.raises(ProviderError):
        async for token in provider.stream(LLMRequest(prompt="hello")):
            received.append(token)

    # Tokens emitted before the failure still arrive (partial output is
    # delivered, then a clean typed error terminates the stream).
    assert received == ["partial"]


@pytest.mark.asyncio
async def test_stream_survives_malformed_chunks():
    create_mock = AsyncMock(
        return_value=_FakeAsyncStream(
            [
                SimpleNamespace(choices=[]),        # no choices
                SimpleNamespace(choices=[SimpleNamespace(delta=None)]),  # no delta
                _chunk("ok"),
            ]
        )
    )

    provider = _provider_with_client(create_mock)

    tokens = [token async for token in provider.stream(LLMRequest(prompt="q"))]

    assert tokens == ["ok"]


# ──────────────────────────────────────────────────────────────────────────────
# TokenQuotaEnforcer
# ──────────────────────────────────────────────────────────────────────────────


def test_quota_charges_and_exhausts():
    quota = TokenQuotaEnforcer(daily_limit=100)

    assert quota.consume("u1", 60) is True
    assert quota.remaining("u1") == 40
    # A charge that would exceed the budget is rejected and not applied.
    assert quota.consume("u1", 60) is False
    assert quota.remaining("u1") == 40
    assert quota.consume("u1", 40) is True
    assert quota.remaining("u1") == 0


def test_quota_isolated_per_user():
    quota = TokenQuotaEnforcer(daily_limit=100)

    assert quota.consume("u1", 100) is True
    assert quota.consume("u2", 100) is True
    assert quota.remaining("u1") == 0
    assert quota.remaining("u2") == 0


def test_quota_disabled_when_zero():
    quota = TokenQuotaEnforcer(daily_limit=0)

    assert quota.enabled is False
    assert quota.consume("u1", 10**9) is True
    assert quota.remaining("u1") == -1


# ──────────────────────────────────────────────────────────────────────────────
# ChatService quota enforcement
# ──────────────────────────────────────────────────────────────────────────────


class _FakeUser:
    def __init__(self, user_id: str) -> None:
        self.id = user_id


def _workflow_result():
    return SimpleNamespace(
        message="ok",
        report=SimpleNamespace(body="ok"),
        tickers=["AAPL"],
        model="fake",
        sources=[],
        plan=[],
        tools_used=[],
        intents=[],
        success=True,
    )


@pytest.fixture(autouse=True)
def _reset_quota_singleton():
    reset_token_quota()
    yield
    reset_token_quota()


def _service_with_quota(limit: int):
    settings = MagicMock()
    settings.llm_token_quota_per_user_per_day = limit
    settings.llm_max_tokens = 4096

    coordinator = MagicMock()

    service = ChatService.__new__(ChatService)
    service._settings = settings
    service._coordinator = coordinator
    service._store = MagicMock()

    return service, coordinator


def test_chat_rejects_when_quota_exhausted(monkeypatch):
    service, _ = _service_with_quota(limit=10)
    monkeypatch.setattr(
        chat_service_module,
        "get_token_quota",
        lambda settings: TokenQuotaEnforcer(daily_limit=10),
    )

    request = ChatRequest(message="What is Apple's current price?", ticker="AAPL")

    with pytest.raises(QuotaExceededError):
        service.chat(request, user=_FakeUser("user-1"))


@pytest.mark.asyncio
async def test_stream_emits_quota_error_frame(monkeypatch):
    service, _ = _service_with_quota(limit=10)
    monkeypatch.setattr(
        chat_service_module,
        "get_token_quota",
        lambda settings: TokenQuotaEnforcer(daily_limit=10),
    )

    request = ChatRequest(message="What is Apple's current price?", ticker="AAPL")

    frames = [
        frame
        async for frame in service.stream_chat(request, user=_FakeUser("user-1"))
    ]

    assert len(frames) == 1
    assert "event: error" in frames[0]
    assert "QUOTA_EXCEEDED" in frames[0]


def test_chat_proceeds_within_quota(monkeypatch):
    service, coordinator = _service_with_quota(limit=100_000)
    monkeypatch.setattr(
        chat_service_module,
        "get_token_quota",
        lambda settings: TokenQuotaEnforcer(daily_limit=100_000),
    )
    coordinator.run.return_value = _workflow_result()

    response = service.chat(
        ChatRequest(message="hi", ticker="AAPL"), user=_FakeUser("user-1")
    )

    assert response.message == "ok"


def test_unauthenticated_requests_bypass_quota(monkeypatch):
    service, coordinator = _service_with_quota(limit=10)
    monkeypatch.setattr(
        chat_service_module,
        "get_token_quota",
        lambda settings: TokenQuotaEnforcer(daily_limit=10),
    )
    coordinator.run.return_value = _workflow_result()

    response = service.chat(ChatRequest(message="hi", ticker="AAPL"), user=None)

    assert response.message == "ok"