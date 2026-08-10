"""
Yahoo financial statements.

Thin wrapper around ``yfinance`` used to retrieve company-specific
financial statements (income statement, balance sheet, cash flow) and
a company profile. This is the existing financial-data provider; Phase 2
integration simply reuses it to feed the analysis engines.
"""

from __future__ import annotations

import yfinance as yf


class FinancialStatements:

    def income_statement(
        self,
        ticker: str,
    ):

        return yf.Ticker(
            ticker,
        ).financials

    def balance_sheet(
        self,
        ticker: str,
    ):

        return yf.Ticker(
            ticker,
        ).balance_sheet

    def cash_flow(
        self,
        ticker: str,
    ):

        return yf.Ticker(
            ticker,
        ).cashflow

    def profile(
        self,
        ticker: str,
    ) -> dict:
        """
        Return the company profile as exposed by Yahoo Finance.

        Contains company-specific identifiers, sector, industry,
        description and market data such as price and market cap.
        """
        return yf.Ticker(
            ticker,
        ).info
