"""
embedding_service.py

Service for generating embeddings.

Design Decisions:
    - **Graceful degradation**: If the configured embedder (e.g. OpenAI) is
      unavailable or returns an error (missing/invalid API key, network
      failure), the service falls back to a deterministic local embedding so
      the retrieval endpoints never crash. This keeps the application
      functional in development environments without valid API keys.
"""

from __future__ import annotations

import hashlib
import logging

from app.core.config import get_settings
from app.embeddings.openai_embedder import OpenAIEmbedder

logger = logging.getLogger(__name__)

_FALLBACK_DIMENSION = 1536


def _fallback_vector(text: str, dimension: int = _FALLBACK_DIMENSION) -> list[float]:
    """
    Produce a deterministic pseudo-embedding vector from a text string.

    This is a locality-sensitive fallback used only when the primary
    embedding provider is unavailable. It hashes character n-grams into a
    fixed-length vector so that similar texts produce similar vectors.

    Args:
        text: The input text.
        dimension: Length of the generated vector.

    Returns:
        A list of ``dimension`` floats.
    """
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
    """
    High-level embedding service.
    """

    def __init__(self) -> None:
        self.embedder = OpenAIEmbedder()

    def _use_remote(self) -> bool:
        """Use real provider embeddings only when running online (not mock mode)."""
        try:
            return get_settings().llm_provider.lower() != "mock"
        except Exception:
            return True

    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        """
        Embed a single text.

        Args:
            text: The text to embed.

        Returns:
            An embedding vector.
        """
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
        """
        Embed multiple documents.

        Args:
            documents: The documents to embed.

        Returns:
            A list of embedding vectors.
        """
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
