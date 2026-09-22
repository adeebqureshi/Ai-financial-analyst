from __future__ import annotations

import os
from collections.abc import Iterator

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


_MISSING_KEY_MESSAGE = (
    "No LLM API key is configured. Set FREELLMAPI_API_KEY (FreeLLMAPI, "
    "OpenAI-compatible) or OPENAI_API_KEY before enabling the openai "
    "provider, or keep LLM_PROVIDER=mock for offline use."
)


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

        # FreeLLMAPI exposes an OpenAI-compatible API, so it is preferred as
        # the credential source while remaining compatible with a plain
        # OPENAI_API_KEY. `base_url` is injected by the LLM clients from
        # `Settings`; the environment lookup keeps the provider usable when
        # it is constructed directly.
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
                response = self.client.responses.create(
                    model=self.config.model,
                    input=request.prompt,
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_tokens,
                )

            except openai.AuthenticationError as exc:
                raise AuthenticationError(
                    "LLM provider authentication failed "
                    "(invalid or missing API key)."
                ) from exc

            except openai.RateLimitError as exc:
                raise RateLimitError(
                    "LLM provider rate limit exceeded."
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

            output = response.output_text

            return LLMResponse(
                text=output,
                model=self.MODEL,
                usage=TokenUsage(
                    prompt_tokens=len(request.prompt.split()),
                    completion_tokens=len(output.split()),
                ),
            )

        return self.retry.execute(call)

    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[str]:
        response = self.generate(request)

        for token in response.text.split():
            yield token + " "