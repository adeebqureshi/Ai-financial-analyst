"""
Async LLM client tests.

Covers the thin :class:`AsyncOpenAIClient` entry point — provider resolution
from ``ProviderConfig`` and delegation of ``generate`` / ``stream``.
"""

import pytest

from app.llm.async_openai_client import AsyncOpenAIClient
from app.llm.models import LLMRequest
from app.llm.provider_config import ProviderConfig


@pytest.mark.anyio
async def test_async_client_generate_uses_configured_provider():
    client = AsyncOpenAIClient(config=ProviderConfig(provider="mock"))

    response = await client.generate(LLMRequest(prompt="Hello"))

    assert response.model == "mock-llm"
    assert response.text.startswith("LLM_RESPONSE")


@pytest.mark.anyio
async def test_async_client_stream_yields_progressively():
    client = AsyncOpenAIClient(config=ProviderConfig(provider="mock"))

    deltas = [delta async for delta in client.stream(LLMRequest(prompt="Hello"))]

    assert "".join(deltas).startswith("LLM_RESPONSE")
    assert len(deltas) > 1


@pytest.mark.anyio
async def test_async_client_accepts_injected_provider():
    from app.llm.providers.async_mock_provider import AsyncMockLLMProvider

    client = AsyncOpenAIClient(provider=AsyncMockLLMProvider())

    response = await client.generate(LLMRequest(prompt="Hi"))

    assert response.text.startswith("LLM_RESPONSE")
    assert response.model == "mock-llm"
