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
        return yf.Ticker(
            ticker,
        ).info