"""
Simple semantic chunker.
"""

from __future__ import annotations

from app.parsing.chunk import Chunk
from app.parsing.section import Section


class Chunker:
    """
    Splits sections into fixed-size semantic chunks.
    """

    def __init__(
        self,
        chunk_size: int = 150,
    ) -> None:

        self.chunk_size = chunk_size

    def chunk(
        self,
        sections: list[Section],
    ) -> list[Chunk]:

        chunks: list[Chunk] = []

        chunk_id = 0

        for section in sections:

            words = section.content.split()

            for start in range(
                0,
                len(words),
                self.chunk_size,
            ):

                text = " ".join(
                    words[
                        start:start + self.chunk_size
                    ]
                )

                chunks.append(
                    Chunk(
                        id=chunk_id,
                        text=text,
                        section=section.title,
                    )
                )

                chunk_id += 1

        return chunks