from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from app.parsers.base_parser import BaseParser
class HTMLParser(BaseParser):
    def parse_file(
        self,
        file_path: Path,
    ) -> str:
        html = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        return self.parse_text(html)
    def parse_text(
        self,
        text: str,
    ) -> str:
        soup = BeautifulSoup(
            text,
            "lxml",
        )
        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "iframe",
                "svg",
            ]
        ):
            tag.decompose()
        markdown = md(
            str(soup),
            heading_style="ATX",
        )
        lines = []
        for line in markdown.splitlines():
            line = line.rstrip()
            if line:
                lines.append(line)
        return "\n".join(lines)