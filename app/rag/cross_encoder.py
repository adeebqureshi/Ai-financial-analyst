from __future__ import annotations
from abc import ABC
from abc import abstractmethod
class CrossEncoder(ABC):
    @abstractmethod
    def score(
        self,
        query: str,
        document: str,
    ) -> float:
        raise NotImplementedError