from __future__ import annotations
from abc import ABC
from abc import abstractmethod
from app.rag.embedding import Embedding
class VectorStore(ABC):
    @abstractmethod
    def add(
        self,
        embedding: Embedding,
    ) -> None:
        ...
    @abstractmethod
    def search(
        self,
        query: Embedding,
        k: int = 5,
    ) -> list[Embedding]:
        ...
    @abstractmethod
    def clear(self) -> None:
        ...