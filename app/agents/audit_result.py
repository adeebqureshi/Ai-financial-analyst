from __future__ import annotations
from dataclasses import dataclass, field
@dataclass(slots=True)
class AuditResult:
    passed: bool
    issues: list[str]
    notes: list[str] = field(default_factory=list)
    @property
    def issue_count(self) -> int:
        return len(self.issues)