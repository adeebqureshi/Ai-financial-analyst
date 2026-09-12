"""
valuation.py

High-level financial valuation engine.
"""

from __future__ import annotations

from app.financial.dcf import DCFValuation
from app.financial.models import FinancialStatement, ValuationResult
from app.financial.wacc import WACC


class ValuationEngine:

    def evaluate(
        self,
        statement: FinancialStatement,
        current_price: float,
        growth_rate: float,
        risk_free_rate: float,
        beta: float,
        market_return: float,
        tax_rate: float,
        cost_of_debt: float = 0.05,
        terminal_growth: float = 0.03,
        years: int = 5,
    ) -> ValuationResult:
        """
        Run a DCF valuation.

        NOTE: ``cost_of_debt`` (and the rate parameters) should come from the
        canonical :class:`~app.financial.assumptions.FinancialAssumptions` in
        production paths. The defaults here exist only for backward
        compatibility with direct/legacy callers of this engine.

        Args:
            statement: The company's normalized financial statement.
            current_price: Current market price per share (None/0 if unavailable).
            growth_rate: Revenue/FCF growth rate for the projection (decimal).
            risk_free_rate: Risk-free rate (decimal, from FinancialAssumptions).
            beta: Stock beta.
            market_return: Expected market return (decimal, from FinancialAssumptions).
            tax_rate: Effective tax rate (decimal).
            cost_of_debt: Pre-tax cost of debt (decimal, from FinancialAssumptions).
            terminal_growth: Perpetual terminal growth rate (decimal).
            years: Projection horizon in whole years.
        """

        equity = (
            statement.total_assets
            - statement.total_liabilities
        )

        cost_of_equity = WACC.cost_of_equity(
            risk_free_rate=risk_free_rate,
            beta=beta,
            market_return=market_return,
        )

        try:
            discount_rate = WACC.calculate(
                equity=equity,
                debt=statement.debt,
                cost_of_equity=cost_of_equity,
                cost_of_debt=cost_of_debt,
                tax_rate=tax_rate,
            )
        except ValueError:
            discount_rate = cost_of_equity

        # Keep the discount rate above the terminal growth so the DCF
        # terminal value stays finite.
        discount_rate = max(discount_rate, terminal_growth + 0.01)

        # The DCF models free cash flow to the firm (FCFF) discounted at WACC,
        # so it yields enterprise value (EV). Intrinsic *equity* value per share
        # requires subtracting net debt (debt − cash). Using EV/share directly
        # overstates the intrinsic value whenever a company carries debt.
        enterprise_value_per_share = DCFValuation.intrinsic_value(
            free_cash_flow=statement.free_cash_flow,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
            years=years,
            shares_outstanding=statement.shares_outstanding,
        )

        net_debt_per_share = (
            (statement.debt - statement.cash) / statement.shares_outstanding
            if statement.shares_outstanding > 0
            else 0.0
        )

        intrinsic = enterprise_value_per_share - net_debt_per_share

        if current_price > 0:
            upside = (
                (intrinsic - current_price)
                / current_price
            ) * 100
        else:
            upside = 0.0

        if current_price <= 0:
            recommendation = "HOLD"
        elif upside >= 20:
            recommendation = "STRONG BUY"
        elif upside >= 10:
            recommendation = "BUY"
        elif upside >= -10:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"

        return ValuationResult(
            intrinsic_value=intrinsic,
            upside=upside,
            recommendation=recommendation,
        )