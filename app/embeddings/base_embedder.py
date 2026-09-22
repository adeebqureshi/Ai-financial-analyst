from __future__ import annotations
from abc import ABC, abstractmethod
class BaseEmbedder(ABC):
    @abstractmethod
    def embed_text(
        self,
        text: str,
    ) -> list[float]:
    @abstractmethod
    def embed_documents(
        self,
        documents: list[str],
    ) -> list[list[float]]: