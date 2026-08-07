"""
Document hierarchy node.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DocumentNode:
    """
    Represents a node in the document hierarchy.
    """

    level: int
    title: str
    content: str = ""
    children: list["DocumentNode"] = field(default_factory=list)

    def add_child(
        self,
        node: "DocumentNode",
    ) -> None:
        self.children.append(node)

    @property
    def child_count(self) -> int:
        return len(self.children)