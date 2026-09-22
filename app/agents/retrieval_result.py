from __future__ import annotations
from dataclasses import dataclass
@dataclass(slots=True)
class RetrievalResult:
    query: str
    documents: list[str]
    @property
    def count(self) -> int:
        return len(self.documents)