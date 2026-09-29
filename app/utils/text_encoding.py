"""Text-encoding repair for document ingestion.

PDF and HTML extraction occasionally yields text that was decoded with the
wrong codec, producing classic mojibake such as ``Ã©`` or ``â€™`` instead of
``é`` and ``’``. The bytes are still recoverable, so we repair them at the
ingestion boundary rather than letting corrupted text reach the vector store
and the LLM.
"""

from __future__ import annotations

# Markers that only really appear when UTF-8 was decoded as a single-byte
# codec (latin-1 / cp1252). Genuine financial prose does not contain these
# runs, so their density is a reliable signal.
_MOJIBAKE_MARKERS = ("Ã", "Â", "â€", "ð\x9f", "Ð\x9f")


def _marker_count(text: str) -> int:
    return sum(text.count(marker) for marker in _MOJIBAKE_MARKERS)


def looks_like_mojibake(text: str) -> bool:
    """Return True when ``text`` shows a mojibake signature."""
    if not text:
        return False
    markers = _marker_count(text)
    if markers == 0:
        return False
    # Require a small absolute floor so a single stray character in an
    # otherwise clean document does not trigger a rewrite.
    return markers >= 3 or markers / max(len(text), 1) > 0.001


def _repair_once(text: str) -> str | None:
    """Attempt a single decode round trip; return the best candidate.

    Both codecs are tried and the least-corrupted result wins, because
    cp1252 and latin-1 disagree on the 0x80-0x9F range and picking the
    first workable one can leave text only partially recovered.
    """
    best: str | None = None
    best_markers = _marker_count(text)

    for codec in ("cp1252", "latin-1"):
        try:
            candidate = text.encode(codec, errors="strict").decode(
                "utf-8", errors="strict"
            )
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

        markers = _marker_count(candidate)
        if markers < best_markers:
            best = candidate
            best_markers = markers

    return best


def repair_mojibake(text: str, max_passes: int = 4) -> str:
    """Best-effort recovery of text that was decoded with the wrong codec.

    Documents that pass through several extractors are sometimes decoded
    more than once (UTF-8 read as latin-1, then that result read as latin-1
    again), so the repair is applied repeatedly for as long as it keeps
    measurably reducing the corruption. Correctly decoded text carries no
    markers, is never a candidate, and is therefore returned untouched.
    """
    repaired = text
    for _ in range(max_passes):
        candidate = _repair_once(repaired)
        if candidate is None:
            break
        repaired = candidate

    return repaired
