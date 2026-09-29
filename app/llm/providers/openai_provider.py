from __future__ import annotations

import logging
import os
import re

import openai
from openai import OpenAI

from app.llm.exceptions import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
    TimeoutError,
)
from app.llm.models import LLMRequest, LLMResponse
from app.llm.provider_config import ProviderConfig
from app.llm.providers.base import BaseLLMProvider
from app.llm.retry import RetryPolicy
from app.llm.usage import TokenUsage

logger = logging.getLogger(__name__)


_MISSING_KEY_MESSAGE = (
    "No LLM API key is configured. Set FREELLMAPI_API_KEY (FreeLLMAPI, "
    "OpenAI-compatible) or OPENAI_API_KEY before enabling the openai "
    "provider, or keep LLM_PROVIDER=mock for offline use."
)

# Some OpenAI-compatible gateways (e.g. Gemini) do not send a Retry-After
# header, but they do state the wait in the error body, for example
# "Please retry in 17.663192334s."
_RETRY_HINT = re.compile(r"retry in\s+([0-9]+(?:\.[0-9]+)?)\s*s", re.IGNORECASE)


def extract_retry_after(exc: BaseException) -> float | None:
    """Best-effort read of how long the provider wants us to wait."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers is not None:
        raw = headers.get("retry-after") or headers.get("Retry-After")
        if raw:
            try:
                return max(0.0, float(raw))
            except (TypeError, ValueError):
                pass
    match = _RETRY_HINT.search(str(exc))
    if match:
        try:
            return max(0.0, float(match.group(1)))
        except (TypeError, ValueError):
            return None
    return None


class OpenAIProvider(BaseLLMProvider):
    MODEL = "openai"

    def __init__(
        self,
        config: ProviderConfig | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.config = config or ProviderConfig()
        self.retry = RetryPolicy()
        self.client = None

        if api_key is None:
            api_key = (
                os.getenv("FREELLMAPI_API_KEY")
                or os.getenv("OPENAI_API_KEY")
            )

        if base_url is None:
            base_url = os.getenv("FREELLMAPI_BASE_URL")

        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url or None,
                timeout=self.config.timeout,
            )

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        if self.client is None:
            raise ProviderError(_MISSING_KEY_MESSAGE)

        def call() -> LLMResponse:
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": request.prompt}],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )

            except openai.AuthenticationError as exc:
                raise AuthenticationError(
                    "LLM provider authentication failed "
                    "(invalid or missing API key)."
                ) from exc

            except openai.RateLimitError as exc:
                raise RateLimitError(
                    "LLM provider rate limit exceeded.",
                    retry_after=extract_retry_after(exc),
                ) from exc

            except openai.APITimeoutError as exc:
                raise TimeoutError(
                    "LLM provider request timed out."
                ) from exc

            except openai.APIConnectionError as exc:
                raise ProviderError(
                    "LLM provider connection failed."
                ) from exc

            except openai.APIError as exc:
                status = getattr(exc, "status_code", None)
                detail = f" with status {status}" if status else ""
                raise ProviderError(
                    f"LLM provider API error{detail}."
                ) from exc

            output = response.choices[0].message.content

            if not output:
                logger.warning(
                    "LLM provider returned empty content for prompt (first 100 chars): %s...",
                    request.prompt[:100],
                )
                raise ProviderError("LLM provider returned empty content.")

            return LLMResponse(
                text=output,
                model=getattr(response, "model", None) or self.MODEL,
                usage=TokenUsage(
                    prompt_tokens=len(request.prompt.split()),
                    completion_tokens=len(output.split()),
                ),
            )

        return self.retry.execute(call)
