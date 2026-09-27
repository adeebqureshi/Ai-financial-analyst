"""One-off utility: strip comments from source files.

Python: removes '#' comments and all docstrings (module/class/function),
using the `tokenize` + `ast` modules so string literals are never mangled.
Bodies left empty by docstring removal get a `pass` inserted.

Other languages: conservative comment removal that only touches comment
tokens, leaving string contents intact.

Skips virtualenvs, VCS dirs and build output.
"""

from __future__ import annotations

import ast
import io
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build",
    ".vite", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    "storage", "data", "coverage", ".next", "htmlcov",
}

DRY_RUN = "--apply" not in sys.argv


# ── Python ────────────────────────────────────────────────────────────────

def _docstring_spans(source: str) -> list[tuple[int, int, int, int]]:
    """Return (start_line, start_col, end_line, end_col) for every docstring."""
    spans: list[tuple[int, int, int, int]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return spans

    def collect(body: list) -> None:
        if not body:
            return
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            node = first.value
            spans.append(
                (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)
            )

    collect(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            collect(node.body)
    return spans



def _apply_edits(source: str, deletes: set[int], truncates: dict[int, int]) -> str:
    """Rebuild source with whole-line deletes and per-line truncations."""
    out: list[str] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        if lineno in deletes:
            continue
        if lineno in truncates:
            line = line[: truncates[lineno]].rstrip()
            if not line:
                continue
        out.append(line)
    return "\n".join(out).rstrip("\n") + "\n"


def _pass_insert_points(source: str) -> dict[int, int]:
    """Map "insert `pass` after this original line" -> indent.

    Covers defs/classes whose body is only a docstring. Handles multi-line
    signatures, where the line to insert after is the one ending in ':'
    rather than the `def` line itself.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    lines = source.splitlines()
    points: dict[int, int] = {}
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        if len(node.body) != 1:
            continue
        only = node.body[0]
        if not (
            isinstance(only, ast.Expr)
            and isinstance(only.value, ast.Constant)
            and isinstance(only.value.value, str)
        ):
            continue

        def closes(idx: int) -> bool:
            """True if line `idx` ends the block header preceding the body."""
            if lines[idx - 1].rstrip().endswith(":"):
                return True
            head = lines[idx - 1][:only.col_offset].rstrip()
            return head.endswith(":")

        anchor = only.lineno
        while anchor >= 1 and not closes(anchor):
            anchor -= 1
        if anchor < 1 or not closes(anchor):
            continue
        points[anchor] = only.col_offset

    return points


def strip_python(source: str) -> str:
    """Remove comments and docstrings from Python source."""
    lines = source.splitlines()
    deletes: set[int] = set()
    truncates: dict[int, int] = {}

    for start_line, start_col, end_line, end_col in _docstring_spans(source):
        prefix = lines[start_line - 1][:start_col]
        suffix = lines[end_line - 1][end_col:]
        if suffix.strip():
            # Code follows the docstring on the same line; leave it alone.
            continue
        if prefix.strip():
            # Code precedes it (e.g. `def f(): "doc"`); truncate precisely.
            truncates[start_line] = min(truncates.get(start_line, 10**9), start_col)
        else:
            deletes.update(range(start_line, end_line + 1))

    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                truncates[tok.start[0]] = min(
                    truncates.get(tok.start[0], 10**9), tok.start[1]
                )
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass

    # A def/class whose body was only a docstring needs `pass`, since every
    # following line of that body is being deleted. Emit it right after the
    # header line while we still know the original line numbers.
    pass_after = _pass_insert_points(source)

    out: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        if lineno in deletes:
            continue
        if lineno in truncates:
            line = line[: truncates[lineno]].rstrip()
            if not line:
                continue
        out.append(line)
        if lineno in pass_after:
            out.append(" " * (pass_after[lineno] + 4) + "pass")

    return "\n".join(out).rstrip("\n") + "\n"


# ── Other languages ───────────────────────────────────────────────────────

def strip_c_style(source: str) -> str:
    """Remove // and /* */ comments from TS/JS/CSS, respecting string literals."""
    out: list[str] = []
    i = 0
    n = len(source)
    quote = ""
    while i < n:
        ch = source[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(source[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'`":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if source.startswith("//", i):
            while i < n and source[i] != "\n":
                i += 1
            continue
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(ch)
        i += 1
    text = "".join(out)
    return "\n".join(ln.rstrip() for ln in text.splitlines()).rstrip("\n") + "\n"


def strip_hash_lines(source: str) -> str:
    """Remove full-line and safe trailing '#' comments (YAML/TOML/INI/env/SQL)."""
    out: list[str] = []
    for line in source.splitlines():
        if line.lstrip().startswith("#"):
            continue
        for idx, ch in enumerate(line):
            if ch != "#" or idx == 0:
                continue
            if line[idx - 1].isspace() and not any(
                q in line[:idx] for q in "\"'"
            ):
                line = line[:idx].rstrip()
            break
        out.append(line.rstrip())
    return "\n".join(out).rstrip("\n") + "\n"


def strip_html_comments(source: str) -> str:
    """Remove <!-- --> blocks from Markdown/HTML, leaving prose intact."""
    out: list[str] = []
    i = 0
    n = len(source)
    while i < n:
        start = source.find("<!--", i)
        if start == -1:
            out.append(source[i:])
            break
        out.append(source[i:start])
        end = source.find("-->", start + 4)
        if end == -1:
            break
        i = end + 3
        # Preserve line count so surrounding Markdown structure is unchanged.
        newlines = source.count("\n", start, end + 3)
        if newlines:
            out.append("\n" * newlines)
        else:
            out.append(" ")
    return "".join(out)


HANDLERS = {
    ".py": strip_python,
    ".pyi": strip_python,
    ".ts": strip_c_style,
    ".tsx": strip_c_style,
    ".js": strip_c_style,
    ".jsx": strip_c_style,
    ".mjs": strip_c_style,
    ".css": strip_c_style,
    ".yml": strip_hash_lines,
    ".yaml": strip_hash_lines,
    ".toml": strip_hash_lines,
    ".ini": strip_hash_lines,
    ".cfg": strip_hash_lines,
    ".env": strip_hash_lines,
    ".example": strip_hash_lines,
    ".sql": strip_hash_lines,
    ".md": strip_html_comments,
    ".html": strip_html_comments,
}

NAME_ONLY = {".env", ".env.example", ".gitignore", ".dockerignore", "Dockerfile"}


def main() -> None:
    targets: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path == Path(__file__):
            continue
        if path.suffix.lower() in HANDLERS or path.name in NAME_ONLY:
            targets.append(path)

    changed = 0
    for path in sorted(targets):
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        handler = HANDLERS.get(path.suffix.lower()) or strip_hash_lines
        try:
            new = handler(original)
        except Exception as exc:  # noqa: BLE001
            print(f"  SKIP  {path.relative_to(ROOT)}: {exc}")
            continue
        if new != original:
            changed += 1
            print(f"  {'DRY ' if DRY_RUN else 'WROTE'} "
                  f"{path.relative_to(ROOT)}")
            if not DRY_RUN:
                path.write_text(new, encoding="utf-8", newline="\n")

    print(
        f"\n{len(targets)} files scanned, {changed} "
        f"{'would change' if DRY_RUN else 'changed'}."
    )


if __name__ == "__main__":
    main()


