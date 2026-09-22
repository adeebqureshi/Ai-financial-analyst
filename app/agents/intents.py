from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
class AgentIntent(str, Enum):
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
_LITERAL_GROUPS: dict[str, tuple[str, ...]] = {
    "p/e ratio": ("p/e", "pe ratio", "price to earnings"),
    "document": ("10-k", "10k", "10-q", "10q", "20-f", "8-k", "vs."),
}
def _tokenize(text: str) -> list[str]:
    return [token for token in text.split() if token]
def _tokens_match(query_token: str, phrase_token: str) -> bool:
    if query_token == phrase_token:
        return True
    shared = min(len(query_token), len(phrase_token))
    if shared < 4:
        return False
    return query_token[:shared] == phrase_token[:shared]
def _phrase_matches(tokens: list[str], phrase: tuple[str, ...]) -> bool:
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
    norm_tokens = _tokenize(text)
    return any(
        _phrase_matches(norm_tokens, tuple(_tokenize(normalize_query(p))))
        for p in phrases
    )
def _literal_contains(text: str, group_key: str) -> bool:
    for phrase in _LITERAL_GROUPS[group_key]:
        norm_phrase = re.sub(r"[^a-z0-9]", " ", phrase.lower()).strip()
        norm_phrase = f" {norm_phrase} "
        if norm_phrase in text:
            return True
    return False
def _phrase_weight(phrases: tuple[str, ...], text: str) -> int:
    weight = 0
    for phrase in phrases:
        phrase_tokens = tuple(_tokenize(f" {phrase} "))
        if _phrase_matches(_tokenize(text), phrase_tokens):
            weight += len(phrase_tokens)
    return weight
def _has_financial_intent(text: str) -> bool:
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
    intent: AgentIntent
    score: int
    ambiguous: bool = False
class IntentClassifier:
    def classify(
        self,
        query: str,
        document_id: str | None = None,
    ) -> list[AgentIntent]:
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
        if is_price and not has_financial_intent and not is_document:
            return [AgentIntent.MARKET_DATA]
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
        if not intents:
            intents.append(AgentIntent.COMPANY_RESEARCH)
        return intents
    def classify_with_scores(
        self,
        query: str,
        document_id: str | None = None,
    ) -> list[IntentMatch]:
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