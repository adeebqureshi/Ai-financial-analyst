"""Search + canonical resolution over the company directory."""

from __future__ import annotations

import re
from functools import lru_cache

from app.data.company_directory import COMPANIES, COMPANY_BY_TICKER, CompanyInfo

__all__ = [
    "normalize_query",
    "search_companies",
    "resolve_company",
]

_SUFFIX_RE = re.compile(
    r"\b(inc|incorporated|corp|corporation|company|co|ltd|limited|plc|"
    r"holdings?|group|technologies?|technology|platforms?|systems?|"
    r"labs|laboratories|pharmaceuticals?)\b\.?,?",
    re.IGNORECASE,
)


def _strip_noise(value: str) -> str:
    lowered = value.strip().lower()
    lowered = lowered.replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = _SUFFIX_RE.sub(" ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def normalize_query(value: str | None) -> str:
    if not value or not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value.strip())


def _score(company: CompanyInfo, raw: str, norm: str) -> tuple[int, int] | None:
    upper = raw.strip().upper()
    raw_low = raw.strip().lower()
    ticker = company.ticker
    ticker_low = ticker.lower()
    name_low = company.name.lower()
    name_norm = _strip_noise(company.name)
    if upper == ticker:
        return (0, 0)
    if raw.strip() and ticker_low.startswith(raw_low):
        return (1, 0)
    if norm and (norm == name_norm or norm in {_strip_noise(a) for a in company.aliases}):
        return (2, 0)
    if norm:
        words = [w for w in re.split(r"[^a-z0-9]+", name_low) if w]
        alias_words = [w for a in company.aliases for w in re.split(r"[^a-z0-9]+", a.lower()) if w]
        if any(w.startswith(norm) for w in words + alias_words):
            return (3, 0)
        if name_norm.startswith(norm):
            return (4, 0)
        for alias in company.aliases:
            if _strip_noise(alias).startswith(norm):
                return (5, 0)
        if raw_low in ticker_low and len(raw.strip()) >= 1:
            return (6, 0)
        if norm in name_norm or any(norm in _strip_noise(a) for a in company.aliases):
            pos = name_norm.find(norm)
            return (7, pos if pos >= 0 else 999)
    return None


def search_companies(query: str | None, limit: int = 8) -> list[CompanyInfo]:
    q = normalize_query(query)
    if not q:
        return []
    norm = _strip_noise(q)
    if not norm:
        return []
    scored: list[tuple[tuple[int, int], CompanyInfo]] = []
    for company in COMPANIES:
        score = _score(company, q, norm)
        if score is not None:
            scored.append((score, company))
    scored.sort(key=lambda item: (item[0], item[1].ticker))
    seen: set[str] = set()
    out: list[CompanyInfo] = []
    for _, company in scored:
        if company.ticker in seen:
            continue
        seen.add(company.ticker)
        out.append(company)
        if len(out) >= max(1, limit):
            break
    return out


@lru_cache(maxsize=512)
def resolve_company(value: str | None) -> CompanyInfo | None:
    q = normalize_query(value)
    if not q:
        return None
    norm = _strip_noise(q)
    upper = q.upper()
    if upper in COMPANY_BY_TICKER:
        return COMPANY_BY_TICKER[upper]
    for company in COMPANIES:
        alias_norms = {_strip_noise(a) for a in company.aliases}
        if norm and (norm == _strip_noise(company.name) or norm in alias_norms):
            return company
    if norm and len(norm) <= 6:
        for company in COMPANIES:
            if company.ticker.lower() == norm:
                return company
    results = search_companies(q, limit=1)
    if results:
        top = results[0]
        score = _score(top, q, norm)
        if score is not None and score[0] <= 5:
            return top
    return None
