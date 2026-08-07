"""
Sentence Transformer embedding model.
"""

from __future__ import annotations

from sentence_transformers import SentenceTransformer

from app.rag.embedding import Embedding
from app.rag.embedding_model import EmbeddingModel


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    """
    Embedding model backed by SentenceTransformers.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ) -> None:

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(
        self,
        text: str,
    ) -> Embedding:

        vector = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return Embedding(
            text=text,
            vector=vector.tolist(),
        )