from __future__ import annotations
from openai import OpenAI
from app.core.config import settings
from app.embeddings.base_embedder import BaseEmbedder
class OpenAIEmbedder(BaseEmbedder):
    def __init__(self) -> None:
        # FreeLLMAPI is OpenAI-compatible and also serves embeddings, so the
        # same credential/base URL resolution used by the LLM providers applies:
        # a configured FreeLLMAPI wins, otherwise a plain OPENAI_API_KEY.
        api_key = settings.openai_api_key_str
        base_url: str | None = None
        if settings.uses_freellmapi:
            api_key = settings.freellmapi_api_key_str
            base_url = settings.freellmapi_base_url
        self.client: OpenAI | None = None
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url or None,
            )
        self.model = settings.embedding_model
    def _require_client(self) -> OpenAI:
        if self.client is None:
            raise RuntimeError(
                "No embedding credentials configured. Set FREELLMAPI_API_KEY "
                "(OpenAI-compatible) or OPENAI_API_KEY."
            )
        return self.client
    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        response = self._require_client().embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        response = self._require_client().embeddings.create(
            model=self.model,
            input=documents,
        )
        return [
            item.embedding
            for item in response.data
        ]