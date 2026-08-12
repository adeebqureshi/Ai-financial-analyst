"""
Async LLM provider tests.

Covers the :class:`AsyncLLMProvider` contract, the real
:class:`AsyncOpenAIProvider` (with the SDK client mocked) and the offline
:class:`AsyncMockLLMProvider`.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.llm.async_interfaces import AsyncLLMProvider
from app.llm.exceptions import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
    TimeoutError,
)
from app.llm.models import LLMRequest
from app.llm.providers.async_mock_provider import AsyncMockLLMProvider
from app.llm.providers.async_openai_provider import AsyncOpenAIProvider


class _FakeRequest:
    headers = {}

    def __init__(self) -> None:
        pass


class _FakeResponse:
    status_code = 429
    headers = {}
    request = _FakeRequest()


class _FakeAsyncStream:
    """Minimal async iterator over OpenAI streaming chunks."""

    def __init__(self, chunks: list) -> None:
        self._chunks = iter(chunks)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._chunks)
        except StopIteration:
            raise StopAsyncIteration from None


def _chunk(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=content))]
    )


# ──────────────────────────────────────────────────────────────────────────
# AsyncLLMProvider contract
# ──────────────────────────────────────────────────────────────────────────


def test_async_llm_provider_is_abstract():
    with pytest.raises(TypeError):
        AsyncLLMProvider()


# ──────────────────────────────────────────────────────────────────────────
# AsyncOpenAIProvider — real provider with the SDK client mocked
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_async_openai_provider_missing_key_fails_fast():
    provider = AsyncOpenAIProvider()

    assert provider.client is None

    with pytest.raises(ProviderError):
        await provider.generate(LLMRequest(prompt="Hello"))

    with pytest.raises(ProviderError):
        async for _ in provider.stream(LLMRequest(prompt="Hello")):
            pass


@patch("app.llm.providers.async_openai_provider.os.getenv", return_value="fake-key")
@patch("app.llm.providers.async_openai_provider.AsyncOpenAI")
@pytest.mark.anyio
async def test_async_openai_provider_generate(mock_async_openai, mock_getenv):
    client = MagicMock()
    mock_async_openai.return_value = client

    completion = SimpleNamespace(
        model="gpt-4.1-mini",
        choices=[SimpleNamespace(message=SimpleNamespace(content="Hello"))],
    )
    client.chat.completions.create = AsyncMock(return_value=completion)

    provider = AsyncOpenAIProvider()

    response = await provider.generate(LLMRequest(prompt="Hi"))

    assert response.text == "Hello"
    assert response.model == "gpt-4.1-mini"
    assert response.usage is not None
    assert response.usage.completion_tokens == 1

    client.chat.completions.create.assert_awaited_once()


@patch("app.llm.providers.async_openai_provider.os.getenv", return_value="fake-key")
@patch("app.llm.providers.async_openai_provider.AsyncOpenAI")
@pytest.mark.anyio
async def test_async_openai_provider_stream_yields_deltas(mock_async_openai, mock_getenv):
    client = MagicMock()
    mock_async_openai.return_value = client

    client.chat.completions.create = AsyncMock(
        return_value=_FakeAsyncStream([_chunk("Hello "), _chunk("world")])
    )

    provider = AsyncOpenAIProvider()

    deltas = []
    async for delta in provider.stream(LLMRequest(prompt="Hi")):
        deltas.append(delta)

    assert "".join(deltas) == "Hello world"

    client.chat.completions.create.assert_awaited_once()


@patch("app.llm.providers.async_openai_provider.os.getenv", return_value="fake-key")
@patch("app.llm.providers.async_openai_provider.AsyncOpenAI")
@pytest.mark.anyio
async def test_async_openai_provider_stream_skips_empty_deltas(mock_async_openai, mock_getenv):
    client = MagicMock()
    mock_async_openai.return_value = client

    client.chat.completions.create = AsyncMock(
        return_value=_FakeAsyncStream([_chunk(None), _chunk("ok")])
    )

    provider = AsyncOpenAIProvider()

    deltas = []
    async for delta in provider.stream(LLMRequest(prompt="Hi")):
        deltas.append(delta)

    assert "".join(deltas) == "ok"


@pytest.mark.anyio
async def test_async_openai_provider_maps_sdk_errors():
    provider = AsyncOpenAIProvider()

    with pytest.raises(AuthenticationError):
        provider._map_error(
            __import__("openai").AuthenticationError(
                "bad key", response=_FakeResponse(), body=None
            )
        )

    with pytest.raises(RateLimitError):
        provider._map_error(
            __import__("openai").RateLimitError(
                "too fast", response=_FakeResponse(), body=None
            )
        )

    with pytest.raises(TimeoutError):
        provider._map_error(__import__("openai").APITimeoutError(_FakeRequest()))

    with pytest.raises(ProviderError):
        provider._map_error(
            __import__("openai").APIError(
                "boom", request=_FakeRequest(), body=None
            )
        )


# ──────────────────────────────────────────────────────────────────────────
# AsyncMockLLMProvider — offline provider
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_async_mock_provider_generate():
    provider = AsyncMockLLMProvider()

    response = await provider.generate(LLMRequest(prompt="Hello"))

    assert response.model == "mock-llm"
    assert response.text.startswith("LLM_RESPONSE")
    assert "Hello" in response.text


@pytest.mark.anyio
async def test_async_mock_provider_stream_progressive():
    provider = AsyncMockLLMProvider()

    deltas = []
    async for delta in provider.stream(LLMRequest(prompt="Hello world")):
        deltas.append(delta)

    assert "".join(deltas) == "LLM_RESPONSE:\n\nHello world"
    assert len(deltas) > 1


@pytest.mark.anyio
async def test_async_mock_provider_stream_preserves_complete_response():
    provider = AsyncMockLLMProvider()

    streamed = "".join([d async for d in provider.stream(LLMRequest(prompt="A B C"))])
    generated = await provider.generate(LLMRequest(prompt="A B C"))

    assert streamed == generated.text
