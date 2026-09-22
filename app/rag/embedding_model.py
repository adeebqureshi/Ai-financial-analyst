from __future__ import annotations
from abc import ABC
from abc import abstractmethod
from app.rag.embedding import Embedding
class EmbeddingModel(ABC):
    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> Embedding: