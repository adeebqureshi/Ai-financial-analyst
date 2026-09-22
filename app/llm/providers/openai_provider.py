from __future__ import annotations
import os
from collections.abc import Iterator
import openai
from openai import OpenAI
from app.llm.exceptions import AuthenticationError, ProviderError, RateLimitError, TimeoutError
from app.llm.models import LLMRequest, LLMResponse
from app.llm.provider_config import ProviderConfig
from app.llm.providers.base import BaseLLMProvider
from app.llm.retry import RetryPolicy
from app.llm.usage import TokenUsage
_MISSING_KEY_MESSAGE = (
    "OPENAI_API_KEY is not set. Set it in the environment (or .env) before "
    "enabling the real provider, or keep LLM_PROVIDER=mock for offline use."
)
class OpenAIProvider(BaseLLMProvider):
    MODEL = "openai"
    def __init__(
        self,
        config: ProviderConfig | None = None,
        api_key: str | None = None,
    ) -> None:
        self.config = config or ProviderConfig()
        self.retry = RetryPolicy()
        self.client = None
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
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
                    "OpenAI authentication failed (invalid or missing API key)."
                ) from exc
            except openai.RateLimitError as exc:
                raise RateLimitError("OpenAI rate limit exceeded.") from exc
            except openai.APITimeoutError as exc:
                raise TimeoutError("OpenAI request timed out.") from exc
            except openai.APIConnectionError as exc:
                raise ProviderError("OpenAI connection failed.") from exc
            except openai.APIError as exc:
                status = getattr(exc, "status_code", None)
                detail = f" with status {status}" if status else ""
                raise ProviderError(f"OpenAI API error{detail}.") from exc
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