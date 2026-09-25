from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Chunk:
    chunk_id: int
    text: str
    section: str
    token_count: int
    page: int = 0


class Chunker:
    """Chunk documents while preserving paragraph/table boundaries when possible."""

    def __init__(self, chunk_size: int = 800, overlap: int = 100) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    @staticmethod
    def _is_table_line(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("|") and stripped.endswith("|")

    @classmethod
    def _is_table_block(cls, block: str) -> bool:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            return False
        table_lines = sum(cls._is_table_line(line) for line in lines)
        separator = any(
            line.startswith("|") and "---" in line
            for line in lines
        )
        return table_lines >= 2 and separator

    def _semantic_blocks(self, text: str) -> list[tuple[str, bool]]:
        """Return paragraph/table blocks; tables are never split across blocks."""
        raw_blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
        if not raw_blocks:
            return []
        return [(block, self._is_table_block(block)) for block in raw_blocks]

    def _word_chunks(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []
        if len(words) <= self.chunk_size:
            return [" ".join(words)]

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start = end - self.overlap
        return chunks

    def chunk_section(self, section_name: str, text: str) -> list[Chunk]:
        blocks = self._semantic_blocks(text)
        if not blocks:
            return []

        chunks: list[Chunk] = []
        current: list[str] = []
        current_words = 0

        def flush() -> None:
            nonlocal current, current_words
            if not current:
                return
            chunk_text = "\n\n".join(current).strip()
            chunks.append(
                Chunk(
                    chunk_id=len(chunks),
                    text=chunk_text,
                    section=section_name,
                    token_count=len(chunk_text.split()),
                )
            )
            current = []
            current_words = 0

        for block, is_table in blocks:
            block_words = len(block.split())

            # A financial table is an atomic semantic unit. If it is larger
            # than chunk_size, keep the complete table rather than splitting
            # rows/columns and destroying its meaning.
            if is_table:
                if current:
                    flush()
                chunks.append(
                    Chunk(
                        chunk_id=len(chunks),
                        text=block,
                        section=section_name,
                        token_count=block_words,
                    )
                )
                continue

            # Oversized prose is split normally, but only after any completed
            # semantic blocks have been flushed.
            if block_words > self.chunk_size:
                if current:
                    flush()
                for piece in self._word_chunks(block):
                    chunks.append(
                        Chunk(
                            chunk_id=len(chunks),
                            text=piece,
                            section=section_name,
                            token_count=len(piece.split()),
                        )
                    )
                continue

            if current and current_words + block_words > self.chunk_size:
                flush()

            current.append(block)
            current_words += block_words

        flush()
        return chunks

    def chunk_document(self, sections: dict[str, str]) -> list[Chunk]:
        results: list[Chunk] = []
        next_chunk = 0
        for section, text in sections.items():
            for chunk in self.chunk_section(section, text):
                chunk.chunk_id = next_chunk
                next_chunk += 1
                results.append(chunk)
        return results

    def chunk_pages(self, pages: list[str], section: str = "Document") -> list[Chunk]:
        results: list[Chunk] = []
        next_chunk = 0
        for page_number, page_text in enumerate(pages, start=1):
            for chunk in self.chunk_section(section, page_text):
                chunk.chunk_id = next_chunk
                chunk.page = page_number
                next_chunk += 1
                results.append(chunk)
        return results
