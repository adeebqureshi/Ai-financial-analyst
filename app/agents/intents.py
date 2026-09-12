"""
intents.py

Intent classification for the agentic financial research pipeline.

The planner uses this classifier to decide *which* existing capabilities are
needed for a question. Classification is fully deterministic — no LLM, no ML
model, no network call — so tool selection stays cheap, reproducible and
testable.

Classification strategy (hybrid, three layers)
----------------------------------------------
1. **Normalization**: lowercasing, contraction expansion ("what's" → "what
   is"), possessive stripping ("apple's" → "apple") and punctuation collapse.
   This alone fixes a class of failures ("bankrupt?" never matched the phrase
   "bankruptcy" because of the trailing punctuation-adjacent form).
2. **Stemmed token matching**: queries and phrases are tokenized; a phrase
   matches when its tokens appear as a contiguous run of query tokens under a
   light prefix rule (a shared prefix of >= 4 characters counts as a match).
   This unifies morphological variants without any NLP dependency:
   ``bankrupt``/``bankruptcy``, ``compare``/``comparing``/``comparison``,
   ``risk``/``risky``/``risks``, ``healthy``/``health``.
   A small set of **literal phrases** (``p/e``, ``10-k``, ``vs.``) that do not
   survive tokenization are matched as raw substrings.
3. **Weighted evidence + ambiguity**: each matched phrase contributes weight
   (multi-word phrases weigh more). The result carries per-intent scores and
   an ``ambiguous`` flag when two or more analytical intents have
   multi-phrase evidence, so callers can surface uncertainty instead of
   silently committing to one reading.

Precedence rules (unchanged from the original design)
-----------------------------------------------------
- ``DOCUMENT_RESEARCH`` questions ("what does the 10-K say about ...") are
  detected first so a bare document question does not accidentally trigger a
  DCF or a risk engine; only an explicit analytical request (the document
  gate) upgrades a document question into a mixed one.
- A pure "what is the current price" question maps to a single
  ``MARKET_DATA`` intent so the planner selects only the market tool.
- A question that names a company but matches nothing specific falls back to
  ``COMPANY_RESEARCH`` (safe: bounded profile/financials evidence, no
  speculative calculations).

Why there is no LLM fallback
----------------------------
The planner's contract is synchronous and deterministic ("never invokes an
LLM") and must remain so: the coordinator runs the planner on every turn and
its LLM usage is async synthesis *after* tools execute. Routing ambiguous
queries to an LLM classifier would add latency, non-determinism and a failure
mode to every request. Ambiguous or unknown queries instead degrade safely:
the union of matched intents is planned (bounded tool registry), and the
auditor rejects answers that are not grounded in retrieved evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class AgentIntent(str, Enum):
    """High-level question intents recognized by the planner."""

    MARKET_DATA = "MARKET_DATA"
    DOCUMENT_RESEARCH = "DOCUMENT_RESEARCH"
    COMPANY_RESEARCH = "COMPANY_RESEARCH"
    FINANCIAL_ANALYSIS = "FINANCIAL_ANALYSIS"
    VALUATION = "VALUATION"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    COMPARISON = "COMPARISON"
    PORTFOLIO_ANALYSIS = "PORTFOLIO_ANALYSIS"
    REPORT_GENERATION = "REPORT_GENERATION"
    CALCULATION = "CALCULATION"


# ──────────────────────────────────────────────────────────────────────────────
# Layer 1 — normalization
# ──────────────────────────────────────────────────────────────────────────────

_CONTRACTIONS = {
    "what's": "what is",
    "whats": "what is",
    "how's": "how is",
    "hows": "how is",
    "it's": "it is",
    "that's": "that is",
    "there's": "there is",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "doesn't": "does not",
    "doesn": "does not",
    "don't": "do not",
    "wont": "will not",
    "won't": "will not",
    "can't": "cannot",
    "cant": "cannot",
    "couldn't": "could not",
    "shouldn't": "should not",
    "wouldn't": "would not",
}

_POSSESSIVE_RE = re.compile(r"([a-z0-9])'s\b")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

# Phrases that only make sense with their punctuation intact (tokenization
# would shred them into meaningless single letters).
_LITERAL_GROUPS: dict[str, tuple[str, ...]] = {
    "p/e ratio": ("p/e", "pe ratio", "price to earnings"),
    "document": ("10-k", "10k", "10-q", "10q", "20-f", "8-k", "vs."),
}




def _tokenize(text: str) -> list[str]:
    """Split a normalized query into lowercase word tokens."""
    return [token for token in text.split() if token]


def _tokens_match(query_token: str, phrase_token: str) -> bool:
    """
    True when a query token matches a phrase token.

    Exact match always wins. Otherwise a shared prefix of at least four
    characters counts as a match, which unifies inflected forms
    (``bankrupt``/``bankruptcy``, ``risks``/``risky``) without a real stemmer.
    Short tokens (< 4 chars) require an exact match to avoid false positives.
    """
    if query_token == phrase_token:
        return True
    shared = min(len(query_token), len(phrase_token))
    if shared < 4:
        return False
    return query_token[:shared] == phrase_token[:shared]


def _phrase_matches(tokens: list[str], phrase: tuple[str, ...]) -> bool:
    """True when ``phrase`` appears as a contiguous run of ``tokens``."""
    size = len(phrase)
    if size == 0 or len(tokens) < size:
        return False
    for start in range(len(tokens) - size + 1):
        if all(
            _tokens_match(tokens[start + offset], phrase_token)
            for offset, phrase_token in enumerate(phrase)
        ):
            return True
    return False

def normalize_query(query: str) -> str:
    """
    Normalize a raw query for classification.
    Lowercases, expands contractions, strips possessives, and collapses
    punctuation/whitespace so phrase matching sees a clean token stream.
    """
    text = query.lower().strip()
    text = _POSSESSIVE_RE.sub(r"\1", text)
    for contraction, expansion in _CONTRACTIONS.items():
        text = re.sub(
            rf"\b{re.escape(contraction)}\b",
            _CONTRACTIONS[contraction],
            text,
        )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return f" {text.strip()} "


# ──────────────────────────────────────────────────────────────────────────────
# Layer 2 — intent phrase knowledge base
# ──────────────────────────────────────────────────────────────────────────────

_PRICE_PHRASES: tuple[str, ...] = (
    "current price",
    "stock price",
    "share price",
    "price of",
    "what is the price",
    "what is the stock price",
    "how much is",
    "trading at",
    "market cap",
    "market capitalization",
    "current share price",
)

_VALUATION_PHRASES: tuple[str, ...] = (
    "is it undervalued",
    "is it overvalued",
    "undervalued",
    "overvalued",
    "fairly valued",
    "dcf",
    "intrinsic value",
    "fair value",
    "price target",
    "what is the intrinsic value",
    "what is the fair value",
    "is the stock cheap",
    "is the stock expensive",
    "is the stock overpriced",
    "valuation",
    "cheap",
    "expensive",
    "upside",
    "good buy",
    "good investment",
    "should i invest",
    "should i buy",
    "buy or sell",
    "recommend",
    "investment thesis",
)

_HEALTH_PHRASES: tuple[str, ...] = (
    "financially healthy",
    "financial health",
    "in good financial shape",
    "financially sound",
    "financially stable",
    "financial strength",
    "financial condition",
    "financial position",
    "solvency",
    "solvent",
    "liquidity",
    "liquid",
    "balance sheet",
    "how healthy",
    "strong balance sheet",
    "weak balance sheet",
    "healthy",
    "sound",
    "stable",
)

_RISK_PHRASES: tuple[str, ...] = (
    "what are the risks",
    "what are the risks of investing",
    "what are the main risks",
    "what could go wrong",
    "what are the downsides",
    "what are the threats",
    "what is the downside",
    "could apple go bankrupt",
    "could it go bankrupt",
    "at risk of bankruptcy",
    "risk of bankruptcy",
    "bankruptcy risk",
    "distress",
    "financial distress",
    "going bankrupt",
    "go bankrupt",
    "is it risky",
    "is it a risky investment",
    "is risky",
    "how risky",
    "risk analysis",
    "risk profile",
    "credit risk",
    "concentration risk",
    "in trouble",
    "in deep trouble",
    "is in trouble",
    "trouble",
    "danger",
    "threat",
    "risky",
    "risks",
    "risk",
)

_COMPARISON_PHRASES: tuple[str, ...] = (
    "compare",
    "comparison",
    "comparing",
    "compare and contrast",
    "which is better",
    "which is best",
    "which is cheaper",
    "which is more expensive",
    "versus",
    " vs ",
    "better investment",
    "better company",
    "stronger company",
    "weaker company",
    "outperform",
    "underperform",
)

_REPORT_PHRASES: tuple[str, ...] = (
    "generate a report",
    "generate report",
    "write a report",
    "create a report",
    "investment thesis",
    "build an investment thesis",
    "research report",
    "investment research report",
)

_PORTFOLIO_PHRASES = (
    "portfolio",
    "my holdings",
    "diversification",
)

_CALCULATION_PHRASES = (
    "calculate",
    "compute",
    "calculation",
    "wacc",
    "weighted average cost of capital",
    "cost of equity",
    "cost of debt",
    "capm",
    "net present value",
    "npv",
    "internal rate of return",
    "irr",
    "cagr",
    "compound annual growth",
    "gordon growth",
    "discounted cash flow",
    "formula",
)

_ANALYSIS_PHRASES = (
    "analyze",
    "analysis",
    "financials",
    "financial statement",
    "financial statements",
    "balance sheet",
    "income statement",
    "cash flow",
    "cash flow statement",
    "fundamentals",
    "margins",
    "profitability",
    "growth",
    "revenue",
    "earnings",
    "how is",
    "how are",
)

# Phrase gate used to decide whether a *document* question also needs
# financial analysis tools. Topic words such as "risk", "revenue" or
# "report" (inside "annual report") must NOT flip a document question into a
# mixed question — only an explicit analytical request may do that.
_DOCUMENT_GATE_PHRASES = (
    "compare",
    "comparison",
    "versus",
    " vs ",
    "analyze",
    "analysis",
    "valuation",
    "undervalued",
    "overvalued",
    "dcf",
    "intrinsic value",
    "fair value",
    "price target",
    "financially healthy",
    "financial health",
    "generate a report",
    "generate report",
    "write a report",
    "create a report",
    "investment thesis",
    "investment research report",
    "portfolio",
)

# Document phrase list: explicit document/research intent signals.
# A question that mentions a specific filing ("10-K", "annual report") or
# explicitly asks for document content is classified as DOCUMENT_RESEARCH.
_DOCUMENT_PHRASES: tuple[str, ...] = (
    "10-k",
    "10k",
    "10-q",
    "10q",
    "annual report",
    "quarterly report",
    "10-k report",
    "annual filings",
    "filing",
    "filings",
    "sec filings",
    "sec filing",
    "what does the 10-k say",
    "what does the 10-q say",
    "what does the report say",
    "what does the filing say",
    "what does the document say",
    "what does it say",
    "mentioned in",
    "according to the",
    "based on the filing",
    "from the annual report",
    "from the 10-k",
    "from the report",
    "in the 10-k",
    "in the annual report",
    "in the filing",
    "report says",
    "filing says",
    "document says",
)



def _matches_any(text: str, phrases: tuple[str, ...]) -> bool:
    """True when ``text`` (already normalized) matches any phrase in ``phrases``."""
    norm_tokens = _tokenize(text)
    return any(
        _phrase_matches(norm_tokens, tuple(_tokenize(normalize_query(p))))
        for p in phrases
    )


def _literal_contains(text: str, group_key: str) -> bool:
    """Match punctuation-bound literal phrases (p/e, 10-k, vs.) as substrings.

    ``text`` has already been normalized by :func:`normalize_query`. Because
    normalization replaces hyphens and other non-alphanumeric characters with
    spaces, hyphenated literal phrases are normalized here too so that e.g.
    "10-k" in the raw query matches "10 k" in the normalized text.
    """
    for phrase in _LITERAL_GROUPS[group_key]:
        norm_phrase = re.sub(r"[^a-z0-9]", " ", phrase.lower()).strip()
        norm_phrase = f" {norm_phrase} "
        if norm_phrase in text:
            return True
    return False


def _phrase_weight(phrases: tuple[str, ...], text: str) -> int:
    """Return an integer weight for matched phrases in ``text``.

    Multi-word phrases are weighted more heavily than single-word phrases because
    they are more specific evidence. This is used to detect ambiguity (two
    different analytical intents both with multi-word evidence) and for testing.
    """
    weight = 0
    for phrase in phrases:
        phrase_tokens = tuple(_tokenize(f" {phrase} "))
        if _phrase_matches(_tokenize(text), phrase_tokens):
            weight += len(phrase_tokens)
    return weight


def _has_financial_intent(text: str) -> bool:
    """True when ``text`` (normalized) contains any analytical intent signal."""
    return any(
        _matches_any(text, phrases)
        for phrases in (
            _VALUATION_PHRASES,
            _HEALTH_PHRASES,
            _RISK_PHRASES,
            _COMPARISON_PHRASES,
            _ANALYSIS_PHRASES,
            _REPORT_PHRASES,
            _PORTFOLIO_PHRASES,
            _CALCULATION_PHRASES,
        )
    )


@dataclass
class IntentMatch:
    """A single matched intent with a scoring/ambiguity snapshot.

    The planner only uses the ``intent`` field for tool selection. The
    ``score`` and ``ambiguous`` fields are exposed on the plan so callers and
    tests can see *why* a query was classified and whether the reading is
    confident or ambiguous — without surfacing raw internals to end users.
    """

    intent: AgentIntent
    score: int
    ambiguous: bool = False


class IntentClassifier:
    """
    Deterministic intent classifier for a user research question.

    Classification is fully deterministic - no LLM, no ML model, no network
    call - so tool selection stays cheap, reproducible and testable.

    Strategy (hybrid, three layers)
    --------------------------------
    1. Normalization: lowercasing, contraction expansion, possessive stripping
       and punctuation collapse. This alone fixes a class of failures
       ("bankrupt?" never matched "bankruptcy" because of trailing punctuation).
    2. Stemmed token matching: queries and phrases are tokenized; a phrase
       matches when its tokens appear as a contiguous run of query tokens under
       a light prefix rule (shared prefix >= 4 chars counts as a match). This
       unifies morphological variants without any NLP dependency:
       bankrupt/bankruptcy, compare/comparing/comparison,
       risk/risky/risks, healthy/health. A small set of literal phrases
       (p/e, 10-k, vs.) that do not survive tokenization are matched as raw
       substrings.
    3. Weighted evidence + ambiguity: each matched phrase contributes weight
       (multi-word phrases weigh more). The result carries per-intent scores
       and an ambiguous flag when two or more analytical intents have
       multi-phrase evidence, so callers can surface uncertainty instead of
       silently committing to one reading.

    Precedence rules
    ----------------
    - DOCUMENT_RESEARCH questions ("what does the 10-K say about ...") are
      detected first so a bare document question does not accidentally trigger
      a DCF or a risk engine; only an explicit analytical request (the document
      gate) upgrades a document question into a mixed one.
    - A pure "what is the current price" question maps to a single
      MARKET_DATA intent so the planner selects only the market tool.
    - A question that names a company but matches nothing specific falls back
      to COMPANY_RESEARCH (safe: bounded profile/financials evidence, no
      speculative calculations).

    Why there is no LLM fallback
    -----------------------------
    The planner's contract is synchronous and deterministic ("never invokes an
    LLM") and must remain so: the coordinator runs the planner on every turn
    and its LLM usage is async synthesis *after* tools execute. Routing
    ambiguous queries to an LLM classifier would add latency, non-determinism
    and a failure mode to every request. Ambiguous or unknown queries instead
    degrade safely: the union of matched intents is planned (bounded tool
    registry), and the auditor rejects answers that are not grounded in
    retrieved evidence.
    """

    def classify(
        self,
        query: str,
        document_id: str | None = None,
    ) -> list[AgentIntent]:
        """
        Classify a question into one or more agent intents.

        Args:
            query: The user question.
            document_id: Optional document the question is explicitly scoped to.

        Returns:
            An ordered list of :class:`AgentIntent` values. The first entry is
            the dominant intent.
        """
        text = normalize_query(query)


        intents: list[AgentIntent] = []

        is_price = _matches_any(text, _PRICE_PHRASES)

        is_document = (
            bool(document_id)
            or _matches_any(text, _DOCUMENT_PHRASES)
        )

        has_financial_intent = any(
            _matches_any(text, phrases)
            for phrases in (
                _VALUATION_PHRASES,
                _HEALTH_PHRASES,
                _RISK_PHRASES,
                _COMPARISON_PHRASES,
                _ANALYSIS_PHRASES,
                _REPORT_PHRASES,
                _PORTFOLIO_PHRASES,
            )
        )

        # Pure market/price shortcut.
        if is_price and not has_financial_intent and not is_document:
            return [AgentIntent.MARKET_DATA]

        # Document-only questions must stay document-only (no DCF etc),
        # unless the question explicitly asks for an analytical capability.
        if is_document and not _matches_any(text, _DOCUMENT_GATE_PHRASES):
            return [AgentIntent.DOCUMENT_RESEARCH]

        if _matches_any(text, _COMPARISON_PHRASES):
            intents.append(AgentIntent.COMPARISON)

        if is_document:
            intents.append(AgentIntent.DOCUMENT_RESEARCH)

        if _matches_any(text, _VALUATION_PHRASES):
            intents.append(AgentIntent.VALUATION)

        if _matches_any(text, _HEALTH_PHRASES):
            intents.append(AgentIntent.FINANCIAL_ANALYSIS)

        if _matches_any(text, _RISK_PHRASES):
            intents.append(AgentIntent.RISK_ANALYSIS)

        if _matches_any(text, _PORTFOLIO_PHRASES):
            intents.append(AgentIntent.PORTFOLIO_ANALYSIS)

        if _matches_any(text, _REPORT_PHRASES):
            intents.append(AgentIntent.REPORT_GENERATION)

        if (
            _matches_any(text, _ANALYSIS_PHRASES)
            and AgentIntent.FINANCIAL_ANALYSIS not in intents
        ):
            intents.append(AgentIntent.FINANCIAL_ANALYSIS)

        if _matches_any(text, _CALCULATION_PHRASES):
            intents.append(AgentIntent.CALCULATION)

        # Company research fallback: a question that names a company but does
        # not map to any specific analysis capability.
        if not intents:
            intents.append(AgentIntent.COMPANY_RESEARCH)

        return intents

    def classify_with_scores(
        self,
        query: str,
        document_id: str | None = None,
    ) -> list[IntentMatch]:
        """
        Classify a question and return scored/ambiguity-annotated matches.

        The ``intent`` sequence is identical to what :meth:`classify` returns;
        ``score`` reflects the weighted phrase evidence and ``ambiguous`` flags
        queries where two or more analytical intents have multi-word evidence.
        Used by tests and by callers that want to inspect *why* a query was
        classified.
        """
        text = normalize_query(query)
        is_price = _matches_any(text, _PRICE_PHRASES)
        is_document = bool(document_id) or _matches_any(text, _DOCUMENT_PHRASES)

        if is_price and not _has_financial_intent(text) and not is_document:
            return [IntentMatch(AgentIntent.MARKET_DATA, 1)]

        if is_document and not _matches_any(text, _DOCUMENT_GATE_PHRASES):
            return [IntentMatch(AgentIntent.DOCUMENT_RESEARCH, 1)]

        matches: list[IntentMatch] = []
        seen: set[AgentIntent] = set()

        def _add(intent: AgentIntent, phrases: tuple[str, ...]) -> None:
            if intent in seen:
                return
            if _matches_any(text, phrases):
                seen.add(intent)
                matches.append(IntentMatch(intent, _phrase_weight(phrases, text)))

        _add(AgentIntent.COMPARISON, _COMPARISON_PHRASES)

        if is_document:
            seen.add(AgentIntent.DOCUMENT_RESEARCH)
            matches.append(IntentMatch(AgentIntent.DOCUMENT_RESEARCH, 1))

        _add(AgentIntent.VALUATION, _VALUATION_PHRASES)
        _add(AgentIntent.FINANCIAL_ANALYSIS, _HEALTH_PHRASES)
        _add(AgentIntent.RISK_ANALYSIS, _RISK_PHRASES)
        _add(AgentIntent.PORTFOLIO_ANALYSIS, _PORTFOLIO_PHRASES)
        _add(AgentIntent.REPORT_GENERATION, _REPORT_PHRASES)

        if (
            _matches_any(text, _ANALYSIS_PHRASES)
            and AgentIntent.FINANCIAL_ANALYSIS not in seen
        ):
            seen.add(AgentIntent.FINANCIAL_ANALYSIS)
            matches.append(IntentMatch(AgentIntent.FINANCIAL_ANALYSIS, 1))

        _add(AgentIntent.CALCULATION, _CALCULATION_PHRASES)

        if not matches:
            matches.append(IntentMatch(AgentIntent.COMPANY_RESEARCH, 0))

        analytical = {
            AgentIntent.VALUATION,
            AgentIntent.FINANCIAL_ANALYSIS,
            AgentIntent.RISK_ANALYSIS,
            AgentIntent.COMPARISON,
            AgentIntent.PORTFOLIO_ANALYSIS,
            AgentIntent.REPORT_GENERATION,
        }
        high_evidence = [
            m for m in matches if m.intent in analytical and m.score >= 2
        ]
        for m in matches:
            m.ambiguous = len(high_evidence) >= 2

        return matches
