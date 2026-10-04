"""Render a completed company analysis into a professional PDF document.

This module is deliberately *pure rendering*. It receives the analysis result
that the workspace has already computed and lays it out as a document. It does
not fetch market data, run a valuation model, call an LLM, or touch the vector
store -- re-running the analysis on download would be slow, expensive and would
risk a PDF that disagrees with the numbers on screen.

Layout is delegated to PyMuPDF's ``Story`` engine (already a project dependency
for PDF parsing), which gives real text flow, automatic pagination and table
support, so the result is a document rather than a screenshot of a web page.

Every value written here comes from the payload. Fields the provider did not
return are rendered as "Not available" -- never as zero and never guessed.
"""

from __future__ import annotations

import html
import io
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pymupdf

# A4 portrait in points, with a 56pt margin on every side.
PAGE = pymupdf.Rect(0, 0, 595, 842)
BODY = pymupdf.Rect(56, 56, 539, 786)

INK = "#111111"
MUTED = "#5f5f5f"
RULE = "#d4d4d4"
BAND = "#f4f4f4"
ACCENT = "#1f1f1f"

NOT_AVAILABLE = "Not available"


class PdfReportError(Exception):
    """Raised when the document cannot be rendered."""


# --------------------------------------------------------------------------
# formatting
# --------------------------------------------------------------------------


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def esc(value: Any) -> str:
    """Escape provider-supplied text before it enters the document."""
    return html.escape(str(value), quote=True)


def opt(value: Any) -> str:
    """Render a value, or an honest marker when the provider omitted it."""
    if value is None or value == "":
        return NOT_AVAILABLE
    return esc(value)


def currency(value: Any, currency_code: str = "USD") -> str:
    if not _is_number(value):
        return NOT_AVAILABLE
    symbol = "$" if currency_code == "USD" else f"{currency_code} "
    return f"{symbol}{value:,.2f}"


def compact_currency(value: Any, currency_code: str = "USD") -> str:
    """Large figures in the units a reader expects on a financials page."""
    if not _is_number(value):
        return NOT_AVAILABLE
    symbol = "$" if currency_code == "USD" else f"{currency_code} "
    magnitude = abs(value)
    for scale, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if magnitude >= scale:
            return f"{symbol}{value / scale:,.2f}{suffix}"
    return f"{symbol}{value:,.2f}"


def percent(value: Any, signed: bool = False) -> str:
    if not _is_number(value):
        return NOT_AVAILABLE
    return f"{value:+.2f}%" if signed else f"{value:.2f}%"


def ratio(value: Any, places: int = 2) -> str:
    if not _is_number(value):
        return NOT_AVAILABLE
    return f"{value:,.{places}f}"


def integer(value: Any) -> str:
    if not _is_number(value):
        return NOT_AVAILABLE
    return f"{value:,.0f}"


# --------------------------------------------------------------------------
# document CSS -- quiet, print-oriented, no decorative colour
# --------------------------------------------------------------------------

USER_CSS = f"""
* {{ font-family: sans-serif; color: {INK}; }}
body {{ font-size: 9pt; line-height: 1.45; }}

h1.masthead {{ font-size: 8.5pt; letter-spacing: 1.6pt; color: {MUTED};
               margin-bottom: 2pt; }}
h1.title {{ font-size: 21pt; margin-bottom: 2pt; }}
p.company {{ font-size: 12pt; color: {MUTED}; margin-bottom: 10pt; }}

h2 {{ font-size: 10.5pt; margin-top: 16pt; margin-bottom: 5pt;
      padding-bottom: 3pt; border-bottom: 0.7pt solid {RULE};
      /* Never leave a heading stranded at the foot of a page. */
      page-break-after: avoid; }}
p.section-note {{ font-size: 8pt; color: {MUTED}; margin-bottom: 6pt; }}
p {{ margin-bottom: 5pt; }}

table {{ font-size: 8.5pt; border-collapse: collapse; width: 100%; }}
/* Keep a section's metric table whole rather than orphaning a row onto the
   next page, which is what a split table looks like in a printed report. */
table {{ page-break-inside: avoid; }}
th {{ background-color: {BAND}; text-align: left; font-weight: bold;
      padding: 3.5pt 5pt; border-bottom: 0.5pt solid {RULE}; }}
td {{ padding: 3.5pt 5pt; border-bottom: 0.4pt solid {RULE};
      vertical-align: top; }}
/* Metric labels are short by construction. Letting them wrap produced ragged
   two- and three-line labels, so the column is sized to fit them on one line
   and the value column absorbs the remainder. */
td.metric {{ width: 62%; color: {MUTED}; white-space: nowrap; }}
td.value {{ text-align: right; font-weight: bold; white-space: nowrap; }}

dl.meta {{ font-size: 8.5pt; margin-bottom: 2pt; }}
p.callout {{ background-color: {BAND}; padding: 7pt 9pt; font-size: 9pt;
             margin-bottom: 6pt; }}
p.callout strong {{ font-size: 11pt; }}
p.fine {{ font-size: 7.5pt; color: {MUTED}; }}
"""


def _table(rows: list[tuple[str, str]], label: str, note: str | None = None) -> str:
    """Two-column metric/value table. Empty rows are dropped, never faked."""
    cells = [
        f"<tr><td class='metric'>{esc(label_name)}</td><td class='value'>{value}</td></tr>"
        for label_name, value in rows
        if value
    ]
    if not cells:
        return ""
    head = f"<h2>{esc(label)}</h2>"
    if note:
        head += f"<p class='section-note'>{esc(note)}</p>"
    return f"{head}<table><tbody>{''.join(cells)}</tbody></table>"


# --------------------------------------------------------------------------
# sections
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class AnalysisPdfPayload:
    """The already-computed analysis result, as the workspace holds it."""

    ticker: str
    company: dict[str, Any]
    market: dict[str, Any]
    statement: dict[str, Any]
    valuation: dict[str, Any]
    health: dict[str, Any]
    recommendation: str
    risk: dict[str, Any] | None = None

    @property
    def currency(self) -> str:
        code = self.market.get("currency")
        return code if isinstance(code, str) and code else "USD"


def _cover(p: AnalysisPdfPayload, generated: datetime) -> str:
    name = p.company.get("name") or p.ticker
    stamp = generated.strftime("%d %B %Y at %H:%M UTC")

    return f"""
    <h1 class="masthead">AI FINANCIAL ANALYST</h1>
    <h1 class="title">Company Research Report</h1>
    <p class="company">{esc(name)} ({esc(p.ticker)})</p>

    <dl class="meta">
      <p><b>Company:</b> {esc(name)}</p>
      <p><b>Ticker:</b> {esc(p.ticker)}</p>
      <p><b>Generated:</b> {esc(stamp)}</p>
    </dl>
    """


def _executive_summary(p: AnalysisPdfPayload) -> str:
    """The pipeline's own verdict, stated as the numbers that produced it."""
    rec = p.valuation.get("recommendation") or p.recommendation
    health = p.health
    risk_level = (p.risk or {}).get("risk_level")

    drivers = (
        f"Intrinsic value of {currency(p.valuation.get('intrinsic_value'), p.currency)} "
        f"against a market price of {currency(p.valuation.get('current_price'), p.currency)}, "
        f"a {percent(p.valuation.get('upside'), signed=True)} gap. "
        f"Financial health scores {integer(health.get('score'))} "
        f"({opt(health.get('rating'))})."
    )
    if risk_level:
        drivers += f" Overall risk is assessed as {str(risk_level).upper()}."

    return f"""
    <h2>Executive summary</h2>
    <p class="callout"><strong>{esc(str(rec).upper())}</strong></p>
    <p>{esc(drivers)}</p>
    <p class="fine">This summary restates the outputs of the quantitative
    pipeline already completed for this ticker. No additional analysis or
    language-model call was made to produce this document.</p>
    """


def _company(p: AnalysisPdfPayload) -> str:
    c = p.company
    rows = [
        ("Company", opt(c.get("name"))),
        ("Ticker", opt(c.get("ticker"))),
        ("Exchange", opt(p.market.get("exchange"))),
        ("Sector", opt(c.get("sector"))),
        ("Industry", opt(c.get("industry"))),
        ("Market capitalisation", compact_currency(c.get("market_cap"), p.currency)),
        ("Currency", opt(p.market.get("currency"))),
    ]
    table = _table(rows, "Company overview")

    description = c.get("description")
    about = ""
    if description:
        about = f"<h2>Business description</h2><p>{esc(description)}</p>"

    return table + about


def _market(p: AnalysisPdfPayload) -> str:
    m = p.market
    rows = [
        ("Current price", currency(m.get("current_price"), p.currency)),
        ("Beta", ratio(m.get("beta"))),
        ("P/E ratio", ratio(m.get("pe_ratio"))),
        ("Earnings per share", currency(m.get("eps"), p.currency)),
        ("Dividend yield", percent(m.get("dividend_yield"))),
        ("52-week high", currency(m.get("week_52_high"), p.currency)),
        ("52-week low", currency(m.get("week_52_low"), p.currency)),
        ("Volume", integer(m.get("volume"))),
    ]
    return _table(rows, "Market data")


def _valuation(p: AnalysisPdfPayload) -> str:
    v = p.valuation
    upside = v.get("upside")
    verdict = (
        "Trading below the modelled intrinsic value."
        if _is_number(upside) and upside > 0
        else "Trading above the modelled intrinsic value."
        if _is_number(upside) and upside < 0
        else "Trading in line with the modelled intrinsic value."
    )
    rows = [
        ("Intrinsic value", currency(v.get("intrinsic_value"), p.currency)),
        ("Current price", currency(v.get("current_price"), p.currency)),
        ("Upside / (downside)", percent(upside, signed=True)),
        ("Valuation status", verdict),
        ("Discount rate", percent(v.get("discount_rate"))),
        ("Recommendation", opt(v.get("recommendation"))),
    ]
    return _table(rows, "Valuation")


def _financial_health(p: AnalysisPdfPayload) -> str:
    h = p.health
    rows = [
        ("Health score", integer(h.get("score"))),
        ("Health rating", opt(h.get("rating"))),
        ("Piotroski F-Score", ratio(h.get("piotroski_score"), 0)),
        ("Altman Z-Score", ratio(h.get("altman_score"))),
        ("Beneish M-Score", ratio(h.get("beneish_score"))),
    ]
    return _table(rows, "Financial health")


def _statements(p: AnalysisPdfPayload) -> str:
    s = p.statement
    rows = [
        ("Revenue", compact_currency(s.get("revenue"), p.currency)),
        ("Operating income", compact_currency(s.get("operating_income"), p.currency)),
        ("Net income", compact_currency(s.get("net_income"), p.currency)),
        ("Free cash flow", compact_currency(s.get("free_cash_flow"), p.currency)),
        ("Total assets", compact_currency(s.get("total_assets"), p.currency)),
        ("Total liabilities", compact_currency(s.get("total_liabilities"), p.currency)),
        ("Cash", compact_currency(s.get("cash"), p.currency)),
        ("Debt", compact_currency(s.get("debt"), p.currency)),
        ("Shares outstanding", integer(s.get("shares_outstanding"))),
    ]
    return _table(rows, "Financial statements")


def _risk(p: AnalysisPdfPayload) -> str:
    risk = p.risk
    if not risk:
        return _table(
            [("Risk assessment", "Not available for this ticker")],
            "Risk analysis",
        )

    rows = [
        ("Overall risk level", opt(risk.get("risk_level")).upper()),
        ("Health score", integer(risk.get("health_score"))),
        ("Health rating", opt(risk.get("health_rating"))),
    ]
    table = _table(rows, "Risk analysis")

    # The three model interpretations are free-form dicts; render whatever the
    # risk service actually returned rather than assuming a fixed shape.
    detail_rows: list[tuple[str, str]] = []
    for key, label in (("piotroski", "Piotroski"), ("altman", "Altman"), ("beneish", "Beneish")):
        block = risk.get(key)
        if not isinstance(block, dict):
            continue
        for name, value in block.items():
            if isinstance(value, bool):
                rendered = "Yes" if value else "No"
            elif _is_number(value):
                rendered = f"{value:,.4f}".rstrip("0").rstrip(".")
            elif isinstance(value, str) and value.strip():
                rendered = value.strip()
            else:
                continue
            detail_rows.append((f"{label} — {name}", rendered))

    return table + _table(detail_rows, "Risk model detail")


def _ai_insights(p: AnalysisPdfPayload) -> str:
    """
    The application's model output for this ticker.

    The analysis response carries a quantitative verdict rather than a written
    narrative, so this section reports that verdict in full rather than
    inventing prose or triggering a second language-model call to fill the gap.
    """
    v = p.valuation
    h = p.health
    risk = p.risk or {}
    rows = [
        ("Model recommendation", opt(v.get("recommendation") or p.recommendation)),
        ("Intrinsic value vs market", percent(v.get("upside"), signed=True)),
        ("Financial health assessment", f"{integer(h.get('score'))} / 100 ({opt(h.get('rating'))})"),
        ("Risk assessment", opt(risk.get("risk_level")).upper()),
    ]
    return _table(rows, "AI insights") + (
        "<p class='fine'>A written, grounded narrative for this company is "
        "available from the AI copilot inside the analysis workspace and from "
        "the research report workflow. Neither is reproduced here, because "
        "generating one would require a second language-model call at download "
        "time.</p>"
    )


def _sources(p: AnalysisPdfPayload) -> str:
    m = p.market
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    parts = [
        f"Analysis generated {generated} from the AI Financial Analyst pipeline.",
        f"Report document produced {generated}.",
    ]
    provider = m.get("provider")
    if provider:
        parts.append(f"Market data provider: {provider}.")
    as_of = m.get("as_of")
    if as_of:
        parts.append(f"Quote timestamp: {as_of}.")
    if m.get("cached"):
        parts.append("Market data was served from the provider cache.")
    if m.get("stale"):
        parts.append("The provider flagged this quote as possibly stale.")

    rows = [("Generated", generated)]
    if provider:
        rows.append(("Market data provider", opt(provider)))
    if as_of:
        rows.append(("Quote timestamp", opt(as_of)))
    rows.append(("Currency", opt(m.get("currency"))))
    rows.append(("Retrieval", "Existing analysis result; no re-computation"))

    return _table(rows, "Data sources") + f"<p class='fine'>{esc(' '.join(parts))}</p>"


def _disclaimer() -> str:
    return (
        "<p class='fine'>This document is an automated summary of model output "
        "for research and educational purposes. It is not investment advice, "
        "and it is not a substitute for the underlying disclosures and filings. "
        "Figures reflect the third-party data available at the time of "
        "generation and may be incomplete or delayed.</p>"
    )


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def build_html(payload: AnalysisPdfPayload, generated: datetime) -> str:
    body = "".join(
        [
            _cover(payload, generated),
            _executive_summary(payload),
            _company(payload),
            _market(payload),
            _valuation(payload),
            _financial_health(payload),
            _statements(payload),
            _risk(payload),
            _ai_insights(payload),
            _sources(payload),
            _disclaimer(),
        ]
    )
    return f"<html><body>{body}</body></html>"


def _stamp(data: bytes, running_title: str) -> bytes:
    """Add the footer rule, running title and page numbers.

    Done as a second pass because the total page count is only known once the
    story has been laid out.
    """
    doc = pymupdf.open(stream=data, filetype="pdf")
    total = doc.page_count

    for index, page in enumerate(doc, start=1):
        page.draw_line(
            pymupdf.Point(BODY.x0, 792),
            pymupdf.Point(BODY.x1, 792),
            color=(0.82, 0.82, 0.82),
            width=0.5,
        )
        page.insert_text(
            (BODY.x0, 806),
            running_title,
            fontsize=7.5,
            color=(0.45, 0.45, 0.45),
        )
        page.insert_text(
            (BODY.x1 - 62, 806),
            f"Page {index} of {total}",
            fontsize=7.5,
            color=(0.45, 0.45, 0.45),
        )

    out = doc.tobytes()
    doc.close()
    return out


def render_analysis_pdf(payload: AnalysisPdfPayload) -> bytes:
    """Render the report and return raw PDF bytes."""
    if not payload.ticker:
        raise PdfReportError("A ticker is required to build a report.")

    generated = datetime.now(timezone.utc)
    story_html = build_html(payload, generated)

    try:
        story = pymupdf.Story(html=story_html, user_css=USER_CSS)
    except Exception as exc:  # pragma: no cover - malformed story
        raise PdfReportError("The report layout could not be prepared.") from exc

    buffer = io.BytesIO()

    try:
        writer = pymupdf.DocumentWriter(buffer)
        more = 1
        while more:
            device = writer.begin_page(PAGE)
            more, _ = story.place(BODY)
            story.draw(device)
            writer.end_page()
        writer.close()
    except Exception as exc:
        raise PdfReportError("The report could not be rendered.") from exc

    raw = buffer.getvalue()
    if not raw.startswith(b"%PDF-"):
        raise PdfReportError("The renderer did not produce a PDF document.")

    name = payload.company.get("name") or payload.ticker
    running_title = f"{payload.ticker} · {name}"[:88]

    return _stamp(raw, running_title)


def build_filename(ticker: str) -> str:
    """
    ``NVDA_Financial_Analysis_Report.pdf``.

    The ticker is sanitised so a hostile or malformed value cannot inject path
    separators or characters that are illegal on a filesystem.
    """
    safe = "".join(ch for ch in str(ticker).upper() if ch.isalnum() or ch in "-_")
    safe = safe.strip("-_") or "COMPANY"
    return f"{safe[:16]}_Financial_Analysis_Report.pdf"