"""
Async OpenAI provider.

Asynchronous OpenAI-compatible provider backed by ``openai.AsyncOpenAI``.
Implements the :class:`AsyncLLMProvider` contract with native token/chunk
streaming via the Chat Completions streaming API.

Design Decisions:
    - **Key read from the environment**: The API key comes from
      ``OPENAI_API_KEY`` (process environment). It is never hardcoded and is
      never included in exceptions or logs.
    - **Real streaming**: ``stream`` uses ``chat.completions.create(stream=True)``
      and yields each content delta as it arrives from the wire — it is never
      faked by splitting a completed response into chunks.
    - **Typed failures**: SDK exceptions are mapped to ``app.llm.exceptions``
      (``AuthenticationError``, ``RateLimitError``, ``TimeoutError``,
      ``ProviderError``) so callers can degrade gracefully instead of crashing.
    - **Fail fast on a missing key**: With no key the provider raises a typed
      error rather than silently echoing the prompt, so a misconfigured
      production deployment is obvious instead of producing garbage answers.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import openai
from openai import AsyncOpenAI

from app.llm.async_interfaces import AsyncLLMProvider
from app.llm.exceptions import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
    TimeoutError,
)
from app.llm.models import LLMRequest, LLMResponse
from app.llm.provider_config import ProviderConfig
from app.llm.usage import TokenUsage

_MISSING_KEY_MESSAGE = (
    "OPENAI_API_KEY is not set. Set it in the environment (or .env) before "
    "enabling the real provider, or keep LLM_PROVIDER=mock for offline use."
)


class AsyncOpenAIProvider(AsyncLLMProvider):

    MODEL = "openai"

    def __init__(
        self,
        config: ProviderConfig | None = None,
        api_key: str | None = None,
    ) -> None:
        self.config = config or ProviderConfig()
        self.client: AsyncOpenAI | None = None

        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")

        if api_key:
            self.client = AsyncOpenAI(
                api_key=api_key,
                timeout=self.config.timeout,
            )

    def _messages(self, request: LLMRequest) -> list[dict[str, str]]:
        """Build the Chat Completions message list for a request."""
        return [{"role": "user", "content": request.prompt}]

    def _require_client(self) -> AsyncOpenAI:
        """
        Return the configured client or raise a typed key-free error.
        """
        if self.client is None:
            raise ProviderError(_MISSING_KEY_MESSAGE)
        return self.client

    @staticmethod
    def _map_error(exc: Exception) -> None:
        """
        Map an OpenAI SDK exception to a typed ``app.llm.exceptions`` error.
        """
        if isinstance(exc, openai.AuthenticationError):
            raise AuthenticationError(
                "OpenAI authentication failed (invalid or missing API key)."
            ) from exc
        if isinstance(exc, openai.RateLimitError):
            raise RateLimitError("OpenAI rate limit exceeded.") from exc
        if isinstance(exc, openai.APITimeoutError):
            raise TimeoutError("OpenAI request timed out.") from exc
        if isinstance(exc, openai.APIConnectionError):
            raise ProviderError("OpenAI connection failed.") from exc
        if isinstance(exc, openai.APIError):
            status = getattr(exc, "status_code", None)
            detail = f" with status {status}" if status else ""
            raise ProviderError(f"OpenAI API error{detail}.") from exc
        raise exc

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        client = self._require_client()

        try:
            completion = await client.chat.completions.create(
                model=self.config.model,
                messages=self._messages(request),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except Exception as exc:
            self._map_error(exc)

        output = completion.choices[0].message.content or ""

        return LLMResponse(
            text=output,
            model=getattr(completion, "model", None) or self.MODEL,
            usage=TokenUsage(
                prompt_tokens=len(request.prompt.split()),
                completion_tokens=len(output.split()),
            ),
        )

    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        client = self._require_client()

        try:
            stream = await client.chat.completions.create(
                model=self.config.model,
                messages=self._messages(request),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
            )
        except Exception as exc:
            self._map_error(exc)

        async for chunk in stream:
            choices = getattr(chunk, "choices", None) or []

            if not choices:
                continue

            delta = getattr(choices[0], "delta", None)

            if delta is None:
                continue

            content = getattr(delta, "content", None)

            if content:
                yield content
