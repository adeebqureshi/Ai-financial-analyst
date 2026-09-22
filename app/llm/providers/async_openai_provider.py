from __future__ import annotations
import os
import time
from collections.abc import AsyncIterator
import openai
from openai import AsyncOpenAI
from app.core.logging import get_logger
from app.llm.async_interfaces import AsyncLLMProvider
from app.llm.exceptions import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
    TimeoutError,
)
from app.llm.models import LLMRequest, LLMResponse
from app.llm.provider_config import ProviderConfig
from app.llm.retry import RetryPolicy
from app.llm.usage import TokenUsage
logger = get_logger("app.llm.openai")
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
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.config = config or ProviderConfig()
        self._retry = retry_policy or RetryPolicy()
        self.client: AsyncOpenAI | None = None
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(
                api_key=api_key,
                timeout=self.config.timeout,
            )
    def _messages(self, request: LLMRequest) -> list[dict[str, str]]:
        return [{"role": "user", "content": request.prompt}]
    def _require_client(self) -> AsyncOpenAI:
        if self.client is None:
            raise ProviderError(_MISSING_KEY_MESSAGE)
        return self.client
    @staticmethod
    def _map_error(exc: Exception) -> None:
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
        start = time.perf_counter()
        try:
            completion = await self._retry.execute_async(
                lambda: client.chat.completions.create(
                    model=self.config.model,
                    messages=self._messages(request),
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            )
        except Exception as exc:
            self._log_failure("generate", exc, start)
            self._map_error(exc)
        output = completion.choices[0].message.content or ""
        self._log_success(
            "generate",
            start,
            usage=getattr(completion, "usage", None),
        )
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
        start = time.perf_counter()
        try:
            stream = await client.chat.completions.create(
                model=self.config.model,
                messages=self._messages(request),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=True,
            )
        except Exception as exc:
            self._log_failure("stream", exc, start)
            self._map_error(exc)
        while True:
            try:
                chunk = await stream.__anext__()
            except StopAsyncIteration:
                break
            except Exception as exc:
                self._map_error(exc)
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            if delta is None:
                continue
            content = getattr(delta, "content", None)
            if content:
                yield content
        self._log_success("stream", start)
    def _log_success(self, operation: str, start: float, usage: object = None) -> None:
        duration_ms = (time.perf_counter() - start) * 1000
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        logger.info(
            "LLM call succeeded: operation=%s model=%s duration_ms=%.0f "
            "prompt_tokens=%s completion_tokens=%s",
            operation,
            self.config.model,
            duration_ms,
            prompt_tokens,
            completion_tokens,
        )
    def _log_failure(self, operation: str, exc: Exception, start: float) -> None:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            "LLM call failed: operation=%s model=%s duration_ms=%.0f "
            "error_type=%s error=%s",
            operation,
            self.config.model,
            duration_ms,
            exc.__class__.__name__,
            exc,
        )