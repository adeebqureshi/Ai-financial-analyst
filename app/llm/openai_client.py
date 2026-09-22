from __future__ import annotations
from collections.abc import Iterator
from app.core.config import Settings, get_settings
from app.llm.models import LLMRequest, LLMResponse
from app.llm.provider_config import ProviderConfig
from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.factory import ProviderFactory
class OpenAIClient:
    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        config: ProviderConfig | None = None,
        settings: Settings | None = None,
    ) -> None:
        settings = settings or get_settings()
        self.config = config or ProviderConfig.from_settings(settings)
        if provider is None:
            factory_kwargs: dict[str, object] = {}
            if self.config.provider.lower() == "openai":
                # The resolved ProviderConfig carries LLM_MODEL/TEMPERATURE/
                # MAX_TOKENS/TIMEOUT; without it the provider would fall back
                # to its own defaults and ignore the configured model.
                factory_kwargs["config"] = self.config
                # FreeLLMAPI is OpenAI-compatible and ships its own base URL
                # and key. Prefer it when configured so the openai provider is
                # pointed at the FreeLLMAPI gateway instead of api.openai.com;
                # otherwise fall back to a plain OPENAI_API_KEY.
                if settings.uses_freellmapi:
                    factory_kwargs["api_key"] = settings.freellmapi_api_key_str
                    factory_kwargs["base_url"] = settings.freellmapi_base_url
                elif settings.openai_api_key_str:
                    factory_kwargs["api_key"] = settings.openai_api_key_str
            provider = ProviderFactory.create(self.config.provider, **factory_kwargs)
        self.provider = provider
    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        return self.provider.generate(request)
    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[str]:
        return self.provider.stream(request)