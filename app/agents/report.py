from __future__ import annotations
from dataclasses import dataclass
@dataclass(slots=True)
class InvestmentReport:
    company: str
    title: str
    body: str
    @property
    def word_count(self) -> int:
        return len(self.body.split())