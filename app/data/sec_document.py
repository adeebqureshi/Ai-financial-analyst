"""
SEC document.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SECDocument:

    url: str

    html: str

    @property
    def length(self) -> int:
        return len(self.html)