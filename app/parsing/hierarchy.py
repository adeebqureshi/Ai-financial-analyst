"""
Document hierarchy builder.
"""

from __future__ import annotations

import re

from app.parsing.node import DocumentNode


class HierarchyBuilder:
    """
    Builds a heading hierarchy from Markdown headings.
    """

    HEADER = re.compile(r"^(#+)\s+(.*)$")

    def build(
        self,
        text: str,
    ) -> DocumentNode:

        root = DocumentNode(
            level=0,
            title="Document",
        )

        stack = [root]

        for line in text.splitlines():

            match = self.HEADER.match(line.strip())

            if not match:
                continue

            level = len(match.group(1))

            title = match.group(2).strip()

            node = DocumentNode(
                level=level,
                title=title,
            )

            while stack and stack[-1].level >= level:
                stack.pop()

            stack[-1].add_child(node)

            stack.append(node)

        return root