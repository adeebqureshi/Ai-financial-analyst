from __future__ import annotations
import hashlib
import logging
from app.core.config import get_settings
from app.embeddings.openai_embedder import OpenAIEmbedder
logger = logging.getLogger(__name__)
_FALLBACK_DIMENSION = 1536
def _fallback_vector(text: str, dimension: int = _FALLBACK_DIMENSION) -> list[float]:
    vector = [0.0] * dimension
    lowered = text.lower().strip()
    if not lowered:
        return vector
    tokens = lowered.split()
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    magnitude = sum(v * v for v in vector) ** 0.5
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
    return vector
class EmbeddingService:
    def __init__(self) -> None:
        self.embedder = OpenAIEmbedder()
    def _use_remote(self) -> bool:
        try:
            return get_settings().llm_provider.lower() != "mock"
        except Exception:
            return True
    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        if not self._use_remote():
            return _fallback_vector(text)
        try:
            return self.embedder.embed_text(text)
        except Exception as exc:
            logger.warning(
                "OpenAI embedding failed (%s); using local fallback.",
                exc,
            )
            return _fallback_vector(text)
    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]:
        if not self._use_remote():
            return [_fallback_vector(doc) for doc in documents]
        try:
            return self.embedder.embed_documents(documents)
        except Exception as exc:
            logger.warning(
                "OpenAI batch embedding failed (%s); using local fallback.",
                exc,
            )
            return [_fallback_vector(doc) for doc in documents]