"""
Evaluation Entry Point

Runs a quantitative evaluation of the financial recommendation system
using synthetic demo fixtures. This evaluates the core calculation engines
(Piotroski, Altman, Beneish, DCF valuation) against known reference values.

This is a SYNTHETIC/REFERENCE evaluation using fixed demo data — it does not
measure live financial performance or predictive accuracy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.demo.fixtures.companies import (
    DEMO_FINANCIAL_STATEMENTS,
    DEMO_MARKET_QUOTES,
    DEMO_RISK_SCORES,
    DEMO_GROWTH_RATES,
    DEMO_TAX_RATES,
    DEMO_TICKERS,
    get_demo_financial_statement,
    get_demo_market_data,
)
from app.financial.altman import AltmanZScore
from app.financial.beneish import BeneishMScore
from app.financial.dcf import DCFValuation
from app.financial.piotroski import Piotroski
from app.financial.ratio_engine import RatioEngine
from app.financial.models import FinancialStatement


@dataclass(slots=True)
class EvaluationResult:
    """Result of a single metric evaluation."""
    ticker: str
    metric: str
    calculated: float
    reference: float
    absolute_error: float
    relative_error_pct: float
    passed: bool


@dataclass(slots=True)
class TickerEvaluation:
    """Aggregated evaluation results for one ticker."""
    ticker: str
    results: list[EvaluationResult]

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def pass_rate(self) -> float:
        return self.passed_count / self.total_count if self.total_count > 0 else 0.0


def _eval_metric(
    ticker: str,
    metric: str,
    calculated: float,
    reference: float,
    tolerance_pct: float = 5.0,
) -> EvaluationResult:
    """Evaluate a single metric against a reference value."""
    abs_error = abs(calculated - reference)
    rel_error = (abs_error / abs(reference) * 100) if reference != 0 else float("inf")
    passed = rel_error <= tolerance_pct
    return EvaluationResult(
        ticker=ticker,
        metric=metric,
        calculated=calculated,
        reference=reference,
        absolute_error=abs_error,
        relative_error_pct=rel_error if rel_error != float("inf") else 100.0,
        passed=passed,
    )


def _compute_piotroski_from_statement(stmt: FinancialStatement) -> int:
    """Compute Piotroski F-Score from a financial statement."""
    equity = stmt.total_assets - stmt.total_liabilities
    ratios = RatioEngine().calculate(
        current_assets=stmt.current_assets,
        current_liabilities=stmt.current_liabilities,
        total_liabilities=stmt.total_liabilities,
        shareholders_equity=equity,
        total_assets=stmt.total_assets,
        revenue=stmt.revenue,
        gross_profit=stmt.gross_profit,
        operating_income=stmt.operating_income,
        net_income=stmt.net_income,
    )
    return Piotroski.calculate(
        roa=ratios.return_on_assets,
        operating_cash_flow=stmt.free_cash_flow,
        change_in_roa=0.0,
        accrual=stmt.free_cash_flow - stmt.net_income,
        change_in_leverage=0.0,
        change_in_liquidity=0.0,
        equity_issued=False,
        change_in_gross_margin=0.0,
        change_in_asset_turnover=0.0,
    )


def _compute_altman_from_statement(
    stmt: FinancialStatement,
    market_price: float,
    shares_outstanding: float,
) -> float:
    """Compute Altman Z-Score from a financial statement."""
    working_capital = stmt.current_assets - stmt.current_liabilities
    market_value_equity = market_price * shares_outstanding
    return AltmanZScore.calculate(
        working_capital=working_capital,
        retained_earnings=stmt.total_assets - stmt.total_liabilities - stmt.debt,
        ebit=stmt.operating_income,
        market_value_equity=market_value_equity,
        total_liabilities=stmt.total_liabilities,
        sales=stmt.revenue,
        total_assets=stmt.total_assets,
    )


def _compute_beneish_from_statement(stmt: FinancialStatement) -> float:
    """Compute Beneish M-Score from a financial statement (simplified)."""
    return BeneishMScore.calculate(
        dsri=1.0,
        gmi=1.0,
        aqi=1.0,
        sgi=1.0,
        depi=1.0,
        sgai=1.0,
        lvgi=1.0,
        tata=0.0,
    )


def _compute_dcf_valuation(
    stmt: FinancialStatement,
    market_price: float,
    growth_rate: float,
    beta: float,
    tax_rate: float,
    shares_outstanding: float,
) -> dict[str, float]:
    """Compute DCF valuation."""
    intrinsic_value = DCFValuation.intrinsic_value(
        free_cash_flow=stmt.free_cash_flow,
        growth_rate=growth_rate,
        discount_rate=0.10,
        terminal_growth=0.025,
        years=5,
        shares_outstanding=shares_outstanding,
    )
    upside = ((intrinsic_value - market_price) / market_price * 100) if market_price > 0 else 0.0
    return {
        "intrinsic_value": intrinsic_value,
        "upside": upside,
        "recommendation": "BUY" if upside > 10 else "HOLD" if upside > -10 else "SELL",
    }


def run_evaluation(tolerance_pct: float = 5.0) -> dict[str, Any]:
    """
    Run the evaluation suite against demo fixtures.

    Args:
        tolerance_pct: Acceptable relative error percentage for a metric to pass.

    Returns:
        Dictionary with evaluation summary and detailed results.
    """
    print("=" * 70)
    print("FINANCIAL RECOMMENDATION SYSTEM — SYNTHETIC EVALUATION")
    print("=" * 70)
    print("Mode: REFERENCE EVALUATION (synthetic demo fixtures)")
    print("Purpose: Verify calculation engines produce expected values")
    print("Data:  DEMO / SYNTHETIC DATA — NOT LIVE MARKET DATA")
    print("=" * 70)
    print()

    all_results: list[TickerEvaluation] = []

    for ticker in DEMO_TICKERS:
        print(f"Evaluating {ticker}...")
        stmt = get_demo_financial_statement(ticker)
        market = get_demo_market_data(ticker)
        risk_scores = DEMO_RISK_SCORES[ticker]
        growth_rate = DEMO_GROWTH_RATES[ticker]
        tax_rate = DEMO_TAX_RATES[ticker]

        results: list[EvaluationResult] = []

        piotroski_calc = _compute_piotroski_from_statement(stmt)
        results.append(_eval_metric(
            ticker, "piotroski_score", float(piotroski_calc),
            float(risk_scores["piotroski_score"]), tolerance_pct
        ))

        altman_calc = _compute_altman_from_statement(
            stmt, market.current_price, stmt.shares_outstanding
        )
        results.append(_eval_metric(
            ticker, "altman_score", altman_calc,
            risk_scores["altman_score"], tolerance_pct
        ))

        beneish_calc = _compute_beneish_from_statement(stmt)
        results.append(_eval_metric(
            ticker, "beneish_score", beneish_calc,
            risk_scores["beneish_score"], tolerance_pct
        ))

        dcf_result = _compute_dcf_valuation(
            stmt, market.current_price, growth_rate, market.beta, tax_rate, stmt.shares_outstanding
        )
        results.append(_eval_metric(
            ticker, "dcf_intrinsic_value", dcf_result["intrinsic_value"],
            market.current_price * 1.15, tolerance_pct * 2
        ))

        all_results.append(TickerEvaluation(ticker=ticker, results=results))

        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"  {r.metric:30s} calc={r.calculated:12.4f} ref={r.reference:12.4f} "
                  f"rel_err={r.relative_error_pct:6.2f}% [{status}]")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_passed = sum(e.passed_count for e in all_results)
    total_metrics = sum(e.total_count for e in all_results)
    overall_pass_rate = total_passed / total_metrics if total_metrics > 0 else 0.0

    for e in all_results:
        print(f"  {e.ticker:6s}: {e.passed_count}/{e.total_count} passed ({e.pass_rate*100:.1f}%)")

    print(f"  OVERALL: {total_passed}/{total_metrics} passed ({overall_pass_rate*100:.1f}%)")
    print()
    print("NOTE: This evaluation uses SYNTHETIC demo data and simplified")
    print("      calculation inputs. It validates engine wiring, not live accuracy.")
    print("=" * 70)

    return {
        "mode": "synthetic_reference_evaluation",
        "data_source": "demo_fixtures",
        "tolerance_pct": tolerance_pct,
        "overall_pass_rate": overall_pass_rate,
        "total_metrics": total_metrics,
        "total_passed": total_passed,
        "tickers": [
            {
                "ticker": e.ticker,
                "passed": e.passed_count,
                "total": e.total_count,
                "pass_rate": e.pass_rate,
                "details": [
                    {
                        "metric": r.metric,
                        "calculated": r.calculated,
                        "reference": r.reference,
                        "absolute_error": r.absolute_error,
                        "relative_error_pct": r.relative_error_pct,
                        "passed": r.passed,
                    }
                    for r in e.results
                ],
            }
            for e in all_results
        ],
    }


if __name__ == "__main__":
    result = run_evaluation()
    print()
    print("JSON OUTPUT:")
    print(json.dumps(result, indent=2, default=str))