from __future__ import annotations
from dataclasses import dataclass
@dataclass(slots=True)
class Task:
    name: str
    description: str
    @property
    def short_name(self) -> str:
        return self.name.lower().replace(" ", "_")