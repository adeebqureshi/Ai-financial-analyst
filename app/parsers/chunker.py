"""
chunker.py

Split parsed financial documents into RAG-ready chunks.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Chunk:
    """
    Represents one chunk of a parsed document.
    """

    chunk_id: int
    text: str
    section: str
    token_count: int


class Chunker:
    """
    Simple chunking engine.
    """

    def __init__(
        self,
        chunk_size: int = 800,
        overlap: int = 100,
    ) -> None:

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_section(
        self,
        section_name: str,
        text: str,
    ) -> list[Chunk]:

        words = text.split()

        chunks: list[Chunk] = []

        start = 0

        chunk_id = 0

        while start < len(words):

            end = min(
                start + self.chunk_size,
                len(words),
            )

            chunk_words = words[start:end]

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=" ".join(chunk_words),
                    section=section_name,
                    token_count=len(chunk_words),
                )
            )

            chunk_id += 1

            if end == len(words):
                break

            start = end - self.overlap

        return chunks

    def chunk_document(
        self,
        sections: dict[str, str],
    ) -> list[Chunk]:

        results: list[Chunk] = []

        next_chunk = 0

        for section, text in sections.items():

            section_chunks = self.chunk_section(
                section,
                text,
            )

            for chunk in section_chunks:

                chunk.chunk_id = next_chunk

                next_chunk += 1

                results.append(chunk)

        return results