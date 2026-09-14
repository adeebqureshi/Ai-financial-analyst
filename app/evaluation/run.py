"""
Evaluation Entry Point

Runs a quantitative evaluation of the financial calculation engines
(Piotroski, Altman, Beneish, DCF) using complete synthetic multi-period
financial data with independently defined expected reference values.

This is a SYNTHETIC REFERENCE EVALUATION using fixed synthetic data — it does
not measure live financial performance or predictive accuracy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.evaluation.fixtures import (
    EVAL_TICKERS,
    EVAL_DATA,
    MultiPeriodFinancialData,
)
from app.financial.altman import AltmanZScore
from app.financial.beneish import BeneishMScore
from app.financial.dcf import DCFValuation
from app.financial.piotroski import Piotroski
from app.financial.ratio_engine import RatioEngine
from app.financial.assumptions import FinancialAssumptions, DEFAULT_RISK_FREE_RATE, DEFAULT_MARKET_RETURN, DEFAULT_COST_OF_DEBT, DEFAULT_TAX_RATE, DEFAULT_TERMINAL_GROWTH, DEFAULT_PROJECTION_YEARS


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


def _compute_piotroski(data: MultiPeriodFinancialData) -> int:
    """
    Compute Piotroski F-Score from complete multi-period synthetic data.

    Uses the same logic as FinancialDataService._compute_piotroski.
    """
    # ROA = Net Income / Total Assets
    roa_t = data.net_income_t / data.total_assets_t if data.total_assets_t else 0.0
    roa_p = data.net_income_p / data.total_assets_p if data.total_assets_p else 0.0

    # Operating cash flow (current period)
    cfo_t = data.operating_cash_flow_t

    # Change in ROA
    change_in_roa = roa_t - roa_p

    # Accrual = CFO - Net Income
    accrual = cfo_t - data.net_income_t

    # Leverage = Long-term Debt / Total Assets
    leverage_t = data.long_term_debt_t / data.total_assets_t if data.total_assets_t else 0.0
    leverage_p = data.long_term_debt_p / data.total_assets_p if data.total_assets_p else 0.0
    change_in_leverage = leverage_t - leverage_p

    # Liquidity = Current Ratio
    current_t = data.current_assets_t / data.current_liabilities_t if data.current_liabilities_t else 1.0
    current_p = data.current_assets_p / data.current_liabilities_p if data.current_liabilities_p else 1.0
    change_in_liquidity = current_t - current_p

    # Equity issued
    equity_issued = data.shares_t > data.shares_p

    # Gross margin
    gross_margin_t = data.gross_profit_t / data.revenue_t if data.revenue_t else 0.0
    gross_margin_p = data.gross_profit_p / data.revenue_p if data.revenue_p else 0.0
    change_in_gross_margin = gross_margin_t - gross_margin_p

    # Asset turnover
    asset_turnover_t = data.revenue_t / data.total_assets_t if data.total_assets_t else 0.0
    asset_turnover_p = data.revenue_p / data.total_assets_p if data.total_assets_p else 0.0
    change_in_asset_turnover = asset_turnover_t - asset_turnover_p

    return Piotroski.calculate(
        roa=roa_t,
        operating_cash_flow=cfo_t,
        change_in_roa=change_in_roa,
        accrual=accrual,
        change_in_leverage=change_in_leverage,
        change_in_liquidity=change_in_liquidity,
        equity_issued=equity_issued,
        change_in_gross_margin=change_in_gross_margin,
        change_in_asset_turnover=change_in_asset_turnover,
    )


def _compute_altman(data: MultiPeriodFinancialData) -> float:
    """
    Compute Altman Z-Score from complete synthetic data.

    Uses the same logic as FinancialDataService._compute_altman.
    """
    working_capital = data.current_assets_t - data.current_liabilities_t
    market_value_equity = data.market_price * data.shares_t

    return AltmanZScore.calculate(
        working_capital=working_capital,
        retained_earnings=data.retained_earnings_t,
        ebit=data.operating_income_t,
        market_value_equity=market_value_equity,
        total_liabilities=data.total_liabilities_t,
        sales=data.revenue_t,
        total_assets=data.total_assets_t,
    )


def _compute_beneish(data: MultiPeriodFinancialData) -> float:
    """
    Compute Beneish M-Score from complete multi-period synthetic data.

    Uses the same logic as FinancialDataService._compute_beneish.
    """
    # DSRI = (Receivables_t / Revenue_t) / (Receivables_p / Revenue_p)
    recv_rev_t = data.receivables_t / data.revenue_t if data.revenue_t else 1.0
    recv_rev_p = data.receivables_p / data.revenue_p if data.revenue_p else 1.0
    dsri = recv_rev_t / recv_rev_p if recv_rev_p else 1.0

    # GMI = (COGS_p / Revenue_p) / (COGS_t / Revenue_t)
    cogs_rev_p = data.cogs_p / data.revenue_p if data.revenue_p else 1.0
    cogs_rev_t = data.cogs_t / data.revenue_t if data.revenue_t else 1.0
    gmi = cogs_rev_p / cogs_rev_t if cogs_rev_t else 1.0

    # AQI = (Non-current assets proportion_t) / (Non-current assets proportion_p)
    # Non-current assets = Total Assets - Current Assets - Net PPE
    nca_t = data.total_assets_t - data.current_assets_t - data.net_ppe_t
    nca_p = data.total_assets_p - data.current_assets_p - data.net_ppe_p
    nca_prop_t = nca_t / data.total_assets_t if data.total_assets_t else 0.0
    nca_prop_p = nca_p / data.total_assets_p if data.total_assets_p else 0.0
    aqi = nca_prop_t / nca_prop_p if nca_prop_p else 1.0

    # SGI = Revenue_t / Revenue_p
    sgi = data.revenue_t / data.revenue_p if data.revenue_p else 1.0

    # DEPI = (Depreciation_p / Total Assets_p) / (Depreciation_t / Total Assets_t)
    dep_ta_p = data.depreciation_p / data.total_assets_p if data.total_assets_p else 1.0
    dep_ta_t = data.depreciation_t / data.total_assets_t if data.total_assets_t else 1.0
    depi = dep_ta_p / dep_ta_t if dep_ta_t else 1.0

    # SGAI = (SGA_t / Revenue_t) / (SGA_p / Revenue_p)
    sga_rev_t = data.sga_t / data.revenue_t if data.revenue_t else 1.0
    sga_rev_p = data.sga_p / data.revenue_p if data.revenue_p else 1.0
    sgai = sga_rev_t / sga_rev_p if sga_rev_p else 1.0

    # LVGI = (Liabilities_t / Total Assets_t) / (Liabilities_p / Total Assets_p)
    liab_ta_t = data.total_liabilities_t / data.total_assets_t if data.total_assets_t else 1.0
    liab_ta_p = data.total_liabilities_p / data.total_assets_p if data.total_assets_p else 1.0
    lvgi = liab_ta_t / liab_ta_p if liab_ta_p else 1.0

    # TATA = (Net Income_t - Operating Cash Flow_t) / Total Assets_t
    tata = (data.net_income_t - data.operating_cash_flow_t) / data.total_assets_t if data.total_assets_t else 0.0

    return BeneishMScore.calculate(
        dsri=dsri,
        gmi=gmi,
        aqi=aqi,
        sgi=sgi,
        depi=depi,
        sgai=sgai,
        lvgi=lvgi,
        tata=tata,
    )


def _compute_dcf(data: MultiPeriodFinancialData) -> dict[str, float]:
    """
    Compute DCF valuation using canonical FinancialAssumptions defaults.
    """
    # Build assumptions from defaults (same as production default configuration)
    assumptions = FinancialAssumptions(
        risk_free_rate=DEFAULT_RISK_FREE_RATE,
        market_return=DEFAULT_MARKET_RETURN,
        cost_of_debt=DEFAULT_COST_OF_DEBT,
        tax_rate=DEFAULT_TAX_RATE,
        terminal_growth=DEFAULT_TERMINAL_GROWTH,
        projection_years=DEFAULT_PROJECTION_YEARS,
        source="evaluation_default",
    )

    # Estimate growth rate from synthetic revenue history (CAGR over 2 periods)
    # In reality this would use more periods; here we use the 2-period CAGR
    if data.revenue_p > 0:
        growth_rate = (data.revenue_t / data.revenue_p) - 1
        growth_rate = max(0.005, min(0.30, growth_rate))  # clamp to defaults
    else:
        growth_rate = 0.05

    # Discount rate = WACC approximation
    # For synthetic evaluation, use a fixed reasonable discount rate
    discount_rate = 0.10  # matches DEFAULT_MARKET_RETURN for simplicity

    intrinsic_value = DCFValuation.intrinsic_value(
        free_cash_flow=data.free_cash_flow_t,
        growth_rate=growth_rate,
        discount_rate=discount_rate,
        terminal_growth=assumptions.terminal_growth,
        years=assumptions.projection_years,
        shares_outstanding=data.shares_t,
    )

    upside = ((intrinsic_value - data.market_price) / data.market_price * 100) if data.market_price > 0 else 0.0
    return {
        "intrinsic_value": intrinsic_value,
        "upside": upside,
        "recommendation": "BUY" if upside > 10 else "HOLD" if upside > -10 else "SELL",
    }


def run_evaluation(tolerance_pct: float = 5.0) -> dict[str, Any]:
    """
    Run the evaluation suite against complete synthetic multi-period fixtures.

    Args:
        tolerance_pct: Acceptable relative error percentage for a metric to pass.

    Returns:
        Dictionary with evaluation summary and detailed results.
    """
    print("=" * 70)
    print("FINANCIAL CALCULATION ENGINES — SYNTHETIC REFERENCE EVALUATION")
    print("=" * 70)
    print("Mode: REFERENCE EVALUATION (complete synthetic multi-period data)")
    print("Purpose: Verify calculation engines produce expected values")
    print("Data:  SYNTHETIC / REFERENCE — NOT LIVE MARKET DATA")
    print("=" * 70)
    print()

    all_results: list[TickerEvaluation] = []

    for ticker in EVAL_TICKERS:
        print(f"Evaluating {ticker}...")
        data = EVAL_DATA[ticker]

        results: list[EvaluationResult] = []

        # Piotroski
        piotroski_calc = _compute_piotroski(data)
        results.append(_eval_metric(
            ticker, "piotroski_score", float(piotroski_calc),
            float(data.expected_piotroski), tolerance_pct
        ))

        # Altman
        altman_calc = _compute_altman(data)
        results.append(_eval_metric(
            ticker, "altman_score", altman_calc,
            data.expected_altman, tolerance_pct
        ))

        # Beneish
        beneish_calc = _compute_beneish(data)
        results.append(_eval_metric(
            ticker, "beneish_score", beneish_calc,
            data.expected_beneish, tolerance_pct
        ))

        # DCF
        dcf_result = _compute_dcf(data)
        results.append(_eval_metric(
            ticker, "dcf_intrinsic_value", dcf_result["intrinsic_value"],
            data.expected_dcf_intrinsic, tolerance_pct * 2  # wider tolerance for DCF
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
    print("NOTE: This evaluation uses SYNTHETIC multi-period reference data.")
    print("      It validates engine wiring and numerical stability, NOT live accuracy.")
    print("=" * 70)

    return {
        "mode": "synthetic_reference_evaluation",
        "data_source": "evaluation_fixtures_multi_period",
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