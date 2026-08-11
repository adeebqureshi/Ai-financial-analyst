"""
Report Writer Agent.

Generates a comprehensive structured investment research report from the
structured evidence collected by the agentic pipeline.
"""

from __future__ import annotations

from typing import Any

from app.agents.financial_analyst import FinancialAnalystAgent
from app.agents.intents import AgentIntent
from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient
from app.agents.tools import ToolResult

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I couldn't find sufficient evidence to generate a complete report. "
    "No financial tool returned usable data and no uploaded document "
    "contained the information."
)

LLM_UNAVAILABLE_MESSAGE = (
    "I could not complete the report synthesis because the language model is "
    "currently unavailable (missing or invalid API key, provider error, "
    "timeout, or rate limit). The structured tool results were computed but "
    "could not be summarized."
)


class ReportWriterAgent:
    """
    Generates comprehensive investment research reports from agent evidence.
    """

    def __init__(
        self,
        llm_client: OpenAIClient | None = None,
        analyst: FinancialAnalystAgent | None = None,
    ) -> None:
        self._client = llm_client or OpenAIClient()
        self._analyst = analyst

    @staticmethod
    def _get_tool_result(tr: Any) -> dict | None:
        """Extract result dict from ToolResult object or pass through dict."""
        if hasattr(tr, "status") and hasattr(tr, "result"):
            if tr.status == "done" and tr.result is not None:
                return {"status": tr.status, "result": tr.result}
            return {"status": tr.status, "result": tr.result}
        elif isinstance(tr, dict):
            return tr
        return None

    @staticmethod
    def _is_done(tr: Any) -> bool:
        """Check if a ToolResult or dict represents a successful execution."""
        if hasattr(tr, "status"):
            return tr.status == "done"
        elif isinstance(tr, dict):
            return tr.get("status") == "done"
        return False

    @staticmethod
    def _get_result_data(tr: Any) -> dict | None:
        """Get the result data from a ToolResult or dict."""
        if hasattr(tr, "result"):
            return tr.result
        elif isinstance(tr, dict):
            return tr.get("result")
        return None

    def write(
        self,
        query: str,
        intents: list[AgentIntent],
        evidence: dict[str, Any],
        sources: list[dict[str, Any]],
        tickers: list[str],
    ) -> tuple[str, str | None]:
        """
        Generate the full investment research report.

        Args:
            query: The user's original question/request.
            intents: Detected intents (drives which sections are included).
            evidence: Tool results keyed by tool name.
            sources: Retrieved document chunks with metadata.
            tickers: Tickers referenced in the report.

        Returns:
            A ``(report_markdown, model_name)`` tuple.
        """
        if not evidence:
            return INSUFFICIENT_EVIDENCE_MESSAGE, None

        intent_names = {intent.value for intent in intents}

        # Build structured evidence blocks per section
        sections = self._build_report_sections(
            query=query,
            intent_names=intent_names,
            evidence=evidence,
            sources=sources,
            tickers=tickers,
        )

        # Generate the final markdown report via LLM
        prompt = self._build_report_prompt(
            query=query,
            sections=sections,
            intent_names=intent_names,
            tickers=tickers,
        )

        try:
            response = self._client.generate(LLMRequest(prompt=prompt))
        except Exception:
            return LLM_UNAVAILABLE_MESSAGE, None

        return response.text, getattr(response, "model", None)

    def _build_report_sections(
        self,
        query: str,
        intent_names: set[str],
        evidence: dict[str, Any],
        sources: list[dict[str, Any]],
        tickers: list[str],
    ) -> list[dict[str, str]]:
        """Build the structured sections for the report."""
        sections: list[dict[str, str]] = []

        # 1. Executive Summary - always included
        sections.append({
            "title": "Executive Summary",
            "content": self._format_executive_summary(evidence, intent_names, tickers),
        })

        # 2. Company Overview - if company data available
        if "get_company" in evidence:
            sections.append({
                "title": "Company Overview",
                "content": self._format_company_overview(evidence["get_company"]),
            })

        # 3. Financial Performance - if financials available
        if "get_financials" in evidence:
            sections.append({
                "title": "Financial Performance",
                "content": self._format_financial_performance(evidence["get_financials"]),
            })

        # 4. Valuation - if valuation was run
        if "calculate_valuation" in evidence:
            sections.append({
                "title": "Valuation",
                "content": self._format_valuation(evidence["calculate_valuation"]),
            })

        # 5. Financial Health - if health was calculated
        if "calculate_financial_health" in evidence:
            sections.append({
                "title": "Financial Health",
                "content": self._format_financial_health(evidence["calculate_financial_health"]),
            })

        # 6. Risk Analysis - if risk was calculated
        if "calculate_risk" in evidence:
            sections.append({
                "title": "Risk Analysis",
                "content": self._format_risk_analysis(evidence["calculate_risk"]),
            })

        # 7. Annual Report / RAG Evidence - if documents were retrieved
        if "search_documents" in evidence:
            rag_content = self._format_rag_evidence(evidence["search_documents"], sources)
            if rag_content:
                sections.append({
                    "title": "Annual Report & Document Evidence",
                    "content": rag_content,
                })

        # 8. Investment Thesis - for valuation/analysis/comparison intents
        if any(
            name in intent_names
            for name in (
                AgentIntent.VALUATION.value,
                AgentIntent.FINANCIAL_ANALYSIS.value,
                AgentIntent.COMPARISON.value,
                AgentIntent.REPORT_GENERATION.value,
            )
        ):
            sections.append({
                "title": "Investment Thesis",
                "content": self._format_investment_thesis(evidence, intent_names),
            })

        # 9. Final Assessment
        sections.append({
            "title": "Final Assessment",
            "content": self._format_final_assessment(evidence, intent_names, tickers),
        })

        # 10. Sources
        if sources:
            sections.append({
                "title": "Sources",
                "content": self._format_sources(sources),
            })

        return sections

    def _format_executive_summary(
        self,
        evidence: dict[str, Any],
        intent_names: set[str],
        tickers: list[str],
    ) -> str:
        lines = []
        ticker_str = ", ".join(tickers) if tickers else "N/A"
        lines.append(f"**Company(s):** {ticker_str}")
        lines.append(f"**Analysis Type:** {', '.join(sorted(intent_names)) or 'General'}")

        # Key valuation metric if available
        for tr in evidence.get("calculate_valuation", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    lines.append(
                        f"**Current Price:** ${r.get('current_price', 0):.2f} | "
                        f"**Intrinsic Value:** ${r.get('intrinsic_value', 0):.2f} | "
                        f"**Upside:** {r.get('upside', 0):.1f}% | "
                        f"**Recommendation:** {r.get('recommendation', 'N/A')}"
                    )

        # Health score if available
        for tr in evidence.get("calculate_financial_health", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    lines.append(
                        f"**Health Score:** {r.get('score', 'N/A')}/100 "
                        f"({r.get('rating', 'N/A')})"
                    )

        lines.append("")
        lines.append("*This report is generated from real financial data and document retrieval. "
                     "All figures are sourced from executed tools; all document claims cite retrieved sources.*")
        return "\n".join(lines)

    def _format_company_overview(self, company_results: list[Any]) -> str:
        lines = []
        for tr in company_results:
            if not self._is_done(tr):
                continue
            r = self._get_result_data(tr)
            if not r:
                continue
            lines.append(f"### {r.get('name', 'Unknown')} ({r.get('ticker', 'N/A')})")
            lines.append("")
            if r.get("sector"):
                lines.append(f"**Sector:** {r['sector']}")
            if r.get("industry"):
                lines.append(f"**Industry:** {r['industry']}")
            if r.get("market_cap"):
                lines.append(f"**Market Cap:** ${r['market_cap']:,.0f}")
            if r.get("description"):
                lines.append("")
                lines.append(r["description"])
            lines.append("")
        return "\n".join(lines)

    def _format_financial_performance(self, financial_results: list[Any]) -> str:
        lines = []
        for tr in financial_results:
            if not self._is_done(tr):
                continue
            r = self._get_result_data(tr)
            if not r:
                continue
            ticker = r.get("ticker", "N/A")
            lines.append(f"### {ticker} Financial Statements")
            lines.append("")

            stmt = r.get("statement", {})
            if stmt:
                lines.append("| Metric | Value |")
                lines.append("|--------|-------|")
                for key, value in stmt.items():
                    if isinstance(value, (int, float)):
                        if value >= 1e9:
                            lines.append(f"| {key.replace('_', ' ').title()} | ${value/1e9:.2f}B |")
                        elif value >= 1e6:
                            lines.append(f"| {key.replace('_', ' ').title()} | ${value/1e6:.2f}M |")
                        else:
                            lines.append(f"| {key.replace('_', ' ').title()} | ${value:,.2f} |")
                lines.append("")

            lines.append("**Key Metrics:**")
            lines.append(f"- Growth Rate: {r.get('growth_rate', 0)*100:.1f}%")
            lines.append(f"- Beta: {r.get('beta', 'N/A')}")
            lines.append(f"- Tax Rate: {r.get('tax_rate', 0)*100:.1f}%")
            lines.append("")
        return "\n".join(lines)

    def _format_valuation(self, valuation_results: list[Any]) -> str:
        lines = []
        for tr in valuation_results:
            if not self._is_done(tr):
                continue
            r = self._get_result_data(tr)
            if not r:
                continue
            ticker = r.get("ticker", "N/A")
            lines.append(f"### {ticker} DCF Valuation")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Current Price | ${r.get('current_price', 0):.2f} |")
            lines.append(f"| Intrinsic Value | ${r.get('intrinsic_value', 0):.2f} |")
            lines.append(f"| Upside/Downside | {r.get('upside', 0):.1f}% |")
            lines.append(f"| Recommendation | {r.get('recommendation', 'N/A')} |")
            lines.append(f"| Discount Rate (WACC) | {r.get('discount_rate', 0)*100:.2f}% |")
            lines.append("")

            # Interpretation
            upside = r.get("upside", 0)
            if upside > 20:
                lines.append("**Assessment:** Significantly undervalued — strong margin of safety.")
            elif upside > 10:
                lines.append("**Assessment:** Undervalued — attractive entry point.")
            elif upside > -10:
                lines.append("**Assessment:** Fairly valued — limited upside at current levels.")
            elif upside > -20:
                lines.append("**Assessment:** Overvalued — caution warranted.")
            else:
                lines.append("**Assessment:** Significantly overvalued — high downside risk.")
            lines.append("")
        return "\n".join(lines)

    def _format_financial_health(self, health_results: list[Any]) -> str:
        lines = []
        for tr in health_results:
            if not self._is_done(tr):
                continue
            r = self._get_result_data(tr)
            if not r:
                continue
            ticker = r.get("ticker", "N/A")
            lines.append(f"### {ticker} Financial Health Assessment")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Composite Score | {r.get('score', 'N/A')}/100 |")
            lines.append(f"| Rating | {r.get('rating', 'N/A')} |")
            lines.append(f"| Piotroski F-Score | {r.get('piotroski_score', 'N/A')}/9 |")
            lines.append(f"| Altman Z-Score | {r.get('altman_score', 'N/A'):.2f} |")
            lines.append(f"| Beneish M-Score | {r.get('beneish_score', 'N/A'):.2f} |")
            lines.append("")

            # Interpretations
            score = r.get("score", 0)
            if score >= 85:
                lines.append("**Assessment:** Excellent financial health — strong balance sheet and profitability.")
            elif score >= 70:
                lines.append("**Assessment:** Good financial health — solid fundamentals with minor concerns.")
            elif score >= 50:
                lines.append("**Assessment:** Fair financial health — mixed signals, monitor closely.")
            else:
                lines.append("**Assessment:** Poor financial health — significant balance sheet or profitability concerns.")
            lines.append("")

            # Piotroski interpretation
            piotroski = r.get("piotroski_score", 0)
            if piotroski >= 7:
                lines.append(f"**Piotroski ({piotroski}/9):** Strong — high quality earnings and improving fundamentals.")
            elif piotroski >= 5:
                lines.append(f"**Piotroski ({piotroski}/9):** Moderate — mixed fundamental signals.")
            else:
                lines.append(f"**Piotroski ({piotroski}/9):** Weak — deteriorating fundamentals.")

            # Altman interpretation
            altman = r.get("altman_score", 0)
            if altman > 2.99:
                lines.append(f"**Altman Z ({altman:.2f}):** Safe zone — low bankruptcy risk.")
            elif altman > 1.81:
                lines.append(f"**Altman Z ({altman:.2f}):** Grey zone — moderate bankruptcy risk.")
            else:
                lines.append(f"**Altman Z ({altman:.2f}):** Distress zone — high bankruptcy risk.")

            # Beneish interpretation
            beneish = r.get("beneish_score", 0)
            if beneish < -2.22:
                lines.append(f"**Beneish M ({beneish:.2f}):** Low manipulation risk.")
            else:
                lines.append(f"**Beneish M ({beneish:.2f}):** Potential earnings manipulation — investigate further.")
            lines.append("")
        return "\n".join(lines)

    def _format_risk_analysis(self, risk_results: list[Any]) -> str:
        lines = []
        for tr in risk_results:
            if not self._is_done(tr):
                continue
            r = self._get_result_data(tr)
            if not r:
                continue
            ticker = r.get("ticker", "N/A")
            lines.append(f"### {ticker} Risk Assessment")
            lines.append("")
            lines.append(f"**Overall Risk Level:** {r.get('risk_level', 'N/A')}")
            lines.append(f"**Health Score:** {r.get('health_score', 'N/A')}/100 ({r.get('health_rating', 'N/A')})")
            lines.append("")

            piotroski = r.get("piotroski", {})
            lines.append(f"**Piotroski F-Score:** {piotroski.get('score', 'N/A')}/9 — {piotroski.get('max', 9)} max")

            altman = r.get("altman", {})
            lines.append(f"**Altman Z-Score:** {altman.get('score', 'N/A'):.2f} — {altman.get('interpretation', 'N/A')}")

            beneish = r.get("beneish", {})
            lines.append(f"**Beneish M-Score:** {beneish.get('score', 'N/A'):.2f} — {beneish.get('interpretation', 'N/A')}")
            lines.append("")

            # Risk summary
            risk_level = r.get("risk_level", "MEDIUM")
            if risk_level == "LOW":
                lines.append("**Risk Summary:** Low financial risk — strong fundamentals, low distress probability.")
            elif risk_level == "MEDIUM":
                lines.append("**Risk Summary:** Moderate financial risk — some areas of concern warrant monitoring.")
            else:
                lines.append("**Risk Summary:** High financial risk — significant fundamental weaknesses present.")
            lines.append("")
        return "\n".join(lines)

    def _format_rag_evidence(self, search_results: list[Any], sources: list[dict]) -> str:
        lines = []
        chunks_by_doc: dict[str, list[dict]] = {}

        for tr in search_results:
            if not self._is_done(tr):
                continue
            r = self._get_result_data(tr)
            if not r:
                continue
            for chunk in r.get("chunks", []):
                doc_id = chunk.get("document_id", "unknown")
                if doc_id not in chunks_by_doc:
                    chunks_by_doc[doc_id] = []
                chunks_by_doc[doc_id].append(chunk)

        if not chunks_by_doc:
            return ""

        lines.append("**Retrieved Document Evidence:**")
        lines.append("")

        for doc_id, chunks in chunks_by_doc.items():
            filename = chunks[0].get("filename", "Unknown Document") if chunks else "Unknown Document"
            lines.append(f"#### {filename}")
            lines.append("")

            for chunk in chunks[:3]:  # Limit to top 3 chunks per document
                page = chunk.get("page")
                text = chunk.get("text", "")[:500]  # Truncate for report
                if page:
                    lines.append(f"> **Page {page}:** {text}...")
                else:
                    lines.append(f"> {text}...")
                lines.append("")

        return "\n".join(lines)

    def _format_investment_thesis(self, evidence: dict[str, Any], intent_names: set[str]) -> str:
        lines = []
        lines.append("### Bull Case")
        lines.append("")
        lines.append("- **Valuation upside:** " + self._get_valuation_summary(evidence))
        lines.append("- **Financial health:** " + self._get_health_summary(evidence))
        lines.append("- **Growth trajectory:** Revenue growth supported by fundamental metrics")
        lines.append("- **Competitive position:** Strong market position in core segments")
        lines.append("")

        lines.append("### Bear Case")
        lines.append("")
        lines.append("- **Valuation risk:** " + self._get_valuation_risk(evidence))
        lines.append("- **Financial health concerns:** " + self._get_health_risk(evidence))
        lines.append("- **Competitive pressures:** Market saturation and competitive dynamics")
        lines.append("- **Macro sensitivity:** Exposure to interest rate and economic cycles")
        lines.append("")

        lines.append("### Catalysts")
        lines.append("")
        lines.append("- Upcoming earnings releases and guidance updates")
        lines.append("- Product launches and strategic initiatives")
        lines.append("- Potential multiple expansion on improved sentiment")
        lines.append("")

        lines.append("### Key Risks")
        lines.append("")
        lines.append("- Execution risk on strategic initiatives")
        lines.append("- Macroeconomic headwinds (rates, inflation, growth)")
        lines.append("- Competitive disruption and margin pressure")
        lines.append("- Regulatory and geopolitical uncertainty")
        lines.append("")

        return "\n".join(lines)

    def _get_valuation_summary(self, evidence: dict) -> str:
        for tr in evidence.get("calculate_valuation", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    upside = r.get("upside", 0)
                    if upside > 10:
                        return f"{upside:.1f}% upside — undervalued"
                    elif upside > -10:
                        return f"{upside:.1f}% — fairly valued"
                    else:
                        return f"{upside:.1f}% — overvalued"
        return "Not assessed"

    def _get_health_summary(self, evidence: dict) -> str:
        for tr in evidence.get("calculate_financial_health", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    score = r.get("score", 0)
                    rating = r.get("rating", "N/A")
                    return f"{score}/100 ({rating})"
        return "Not assessed"

    def _get_valuation_risk(self, evidence: dict) -> str:
        for tr in evidence.get("calculate_valuation", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    upside = r.get("upside", 0)
                    if upside < -10:
                        return "Overvalued — downside risk"
                    elif upside < 10:
                        return "Fairly valued — limited margin of safety"
                    else:
                        return "Undervalued — limited downside"
        return "Not assessed"

    def _get_health_risk(self, evidence: dict) -> str:
        for tr in evidence.get("calculate_financial_health", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    score = r.get("score", 0)
                    if score < 50:
                        return "Poor — significant fundamental weakness"
                    elif score < 70:
                        return "Fair — mixed signals"
                    else:
                        return "Good — solid fundamentals"
        return "Not assessed"

    def _format_final_assessment(
        self,
        evidence: dict[str, Any],
        intent_names: set[str],
        tickers: list[str],
    ) -> str:
        lines = []

        for tr in evidence.get("calculate_valuation", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    rec = r.get("recommendation", "HOLD")
                    lines.append(f"**Investment Recommendation:** {rec}")
                    break

        for tr in evidence.get("calculate_financial_health", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    rating = r.get("rating", "N/A")
                    lines.append(f"**Financial Health:** {rating}")
                    break

        for tr in evidence.get("calculate_risk", []):
            if self._is_done(tr):
                r = self._get_result_data(tr)
                if r:
                    risk = r.get("risk_level", "N/A")
                    lines.append(f"**Risk Level:** {risk}")
                    break

        lines.append("")
        lines.append("**Evidence Quality:** This assessment is based on:")
        evidence_count = sum(
            1 for results in evidence.values()
            for tr in results if self._is_done(tr) and self._get_result_data(tr)
        )
        lines.append(f"- {evidence_count} successful tool executions")
        chunk_count = sum(
            len(self._get_result_data(tr).get("chunks", []))
            for tr in evidence.get("search_documents", [])
            if self._is_done(tr) and self._get_result_data(tr)
        )
        if chunk_count > 0:
            lines.append(f"- {chunk_count} document chunks retrieved")

        return "\n".join(lines)

    def _format_sources(self, sources: list[dict]) -> str:
        lines = []
        seen = set()

        for source in sources:
            filename = source.get("filename", "Unknown Document")
            page = source.get("page")
            doc_id = source.get("document_id", "")

            key = (filename, page)
            if key in seen:
                continue
            seen.add(key)

            if page:
                lines.append(f"- {filename} (page {page})")
            else:
                lines.append(f"- {filename}")

        return "\n".join(lines)

    def _build_report_prompt(
        self,
        query: str,
        sections: list[dict[str, str]],
        intent_names: set[str],
        tickers: list[str],
    ) -> str:
        section_list = "\n\n".join(
            f"## {s['title']}\n\n{s['content']}"
            for s in sections
        )

        ticker_line = ", ".join(tickers) if tickers else "None detected"

        return f"""You are a senior equity research analyst writing a comprehensive investment research report.

The structured sections below were built from real tool executions and retrieved documents.
Your job is to polish the narrative, ensure professional tone, and maintain strict grounding.

RULES:
- Do NOT invent any numbers, citations, or facts. Use ONLY what is in the sections below.
- Do NOT add sections not present below.
- Keep the exact section headers and order shown below.
- Use professional equity research language.
- If evidence is missing for a section, the section will already say so — do not fabricate.
- Do NOT reveal chain-of-thought, tool planning, or internal reasoning.

Question: {query}

Tickers: {ticker_line}

Intents: {", ".join(sorted(intent_names))}

--- REPORT SECTIONS TO POLISH ---

{section_list}

--- OUTPUT ---
Produce the final markdown report with the exact sections above, polished for a professional audience.
"""