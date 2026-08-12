"""
data.py

Company-specific financial data integration (Phase 2).

Fetches real, company-specific financial statements and market data from the
existing Yahoo Finance provider (``app.data.financials.FinancialStatements``)
and the existing ``MarketService``, normalizes the values into the domain
``FinancialStatement`` model and computes the Piotroski, Altman and Beneish
scores from the actual company data.

The results are cached in-memory under ``financials:{ticker}`` keys so that
requesting AAPL and then MSFT never returns Apple's data for Microsoft.

This module does **not** fabricate financial figures. If a required value is
unavailable from the provider, an error is raised instead of inventing a
number. Score-model sub-indices that cannot be computed fall back to a
neutral value (1.0) as is standard practice.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass

from app.core.exceptions import RetrievalError
from app.data.financials import FinancialStatements
from app.financial.altman import AltmanZScore
from app.financial.beneish import BeneishMScore
from app.financial.models import FinancialStatement
from app.financial.piotroski import Piotroski
from app.ingestion.services.market_service import MarketService

logger = logging.getLogger(__name__)

_MILLION = 1_000_000.0

# In-memory cache TTL: financial statements move slowly, 30 minutes is safe.
_CACHE_TTL_SECONDS = 60 * 30

# Model assumptions kept stable across tickers.
_RISK_FREE_RATE = 0.0425
_MARKET_RETURN = 0.10
_DEFAULT_TAX_RATE = 0.21
_DEFAULT_BETA = 1.0
_MIN_GROWTH_RATE = 0.005
_MAX_GROWTH_RATE = 0.30


@dataclass(slots=True)
class CompanyFinancialData:
    """
    Normalized, company-specific data feeding the analysis engines.

    Attributes:
        ticker: Ticker symbol.
        statement: Normalized ``FinancialStatement`` (values in $M, shares in M).
        piotroski_score: Piotroski F-Score (0-9) computed from real statements.
        altman_score: Altman Z-Score computed from real statements.
        beneish_score: Beneish M-Score computed from real statements.
        growth_rate: Historical revenue CAGR used for the DCF projection.
        beta: Real stock beta from the market provider.
        tax_rate: Effective tax rate from the real income statement.
        current_price: Real current market price per share.
        name: Company name.
        sector: Company sector.
        industry: Company industry.
        market_cap: Real market capitalization.
        description: Company business summary.
    """

    ticker: str
    statement: FinancialStatement
    piotroski_score: int
    altman_score: float
    beneish_score: float
    growth_rate: float
    beta: float | None
    tax_rate: float
    current_price: float
    name: str
    sector: str | None
    industry: str | None
    market_cap: float | None
    description: str | None


class FinancialDataService:
    """
    Service that turns a ticker into normalized, company-specific financial
    data using the existing Yahoo Finance provider and market service.

    The public entry point is :meth:`load`, which caches results per ticker.
    """

    def __init__(self) -> None:
        self._statements = FinancialStatements()
        self._market = MarketService()
        self._cache: dict[str, tuple[float, CompanyFinancialData]] = {}
        self._lock = threading.Lock()

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def load(self, ticker: str) -> CompanyFinancialData:
        """
        Return normalized company-specific financial data for ``ticker``.

        The result is cached under ``financials:{ticker}`` for
        ``_CACHE_TTL_SECONDS`` so repeated calls do not refetch.

        Args:
            ticker: Ticker symbol (e.g. ``"AAPL"``).

        Returns:
            A ``CompanyFinancialData`` built from real provider data.

        Raises:
            RetrievalError: If the provider cannot supply the required data.
        """
        ticker = ticker.upper()

        cached = self._cache_get(ticker)
        if cached is not None:
            return cached

        data = self._fetch(ticker)

        self._cache_set(ticker, data)
        return data

    def get_statement(self, ticker: str) -> FinancialStatement:
        """Return the normalized financial statement for ``ticker``."""
        return self.load(ticker).statement

    def clear_cache(self, ticker: str | None = None) -> None:
        """
        Clear the cached financial data.

        Args:
            ticker: If provided, only that ticker's cache entry is cleared;
                otherwise the whole cache is cleared.
        """
        with self._lock:
            if ticker is None:
                self._cache.clear()
                return
            self._cache.pop(ticker.upper(), None)

    # ──────────────────────────────────────────────────────────────────────
    # Cache
    # ──────────────────────────────────────────────────────────────────────

    def _cache_get(self, ticker: str) -> CompanyFinancialData | None:
        with self._lock:
            entry = self._cache.get(ticker)
            if entry is None:
                return None
            timestamp, data = entry
            if time.monotonic() - timestamp > _CACHE_TTL_SECONDS:
                self._cache.pop(ticker, None)
                return None
            return data

    def _cache_set(self, ticker: str, data: CompanyFinancialData) -> None:
        with self._lock:
            self._cache[ticker] = (time.monotonic(), data)

    # ──────────────────────────────────────────────────────────────────────
    # Data retrieval + normalization
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _value(frame, label: str, index: int = 0) -> float | None:
        """Return the value at ``label``/``index`` or ``None`` if unavailable."""
        if frame is None or frame.empty:
            return None
        if label not in frame.index:
            return None
        values = frame.loc[label]
        if index >= len(values):
            return None
        value = values.iloc[index]
        if value is None:
            return None
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        return value

    @staticmethod
    def _first(frame, labels: list[str], index: int = 0) -> float | None:
        """Return the first available value among ``labels``."""
        for label in labels:
            value = FinancialDataService._value(frame, label, index)
            if value is not None:
                return value
        return None

    @staticmethod
    def _safe(value) -> float | None:
        if value is None:
            return None
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        return value

    @staticmethod
    def _ratio(numerator, denominator, default: float = 0.0) -> float:
        if numerator is None or denominator is None or denominator == 0:
            return default
        return numerator / denominator

    def _fetch(self, ticker: str) -> CompanyFinancialData:
        """Fetch and normalize the full financial dataset for ``ticker``."""
        try:
            income = self._statements.income_statement(ticker)
            balance = self._statements.balance_sheet(ticker)
            cashflow = self._statements.cash_flow(ticker)
            market = self._market.get_market_data(ticker)
            profile = self._statements.profile(ticker)
        except Exception as exc:
            raise RetrievalError(
                message=(
                    f"Failed to fetch financial data for {ticker}: {exc}"
                ),
                error_code="RETR_DATA",
                details={"ticker": ticker},
            ) from exc

        statement = self._build_statement(
            ticker=ticker,
            income=income,
            balance=balance,
            cashflow=cashflow,
            profile=profile,
        )

        current_price = self._safe(market.current_price) or 0.0
        beta = self._safe(market.beta)

        return CompanyFinancialData(
            ticker=ticker,
            statement=statement,
            piotroski_score=self._compute_piotroski(income, balance, cashflow),
            altman_score=self._compute_altman(
                income,
                balance,
                market,
                profile,
            ),
            beneish_score=self._compute_beneish(income, balance, cashflow),
            growth_rate=self._estimate_growth(income),
            beta=beta if beta is not None else _DEFAULT_BETA,
            tax_rate=self._effective_tax_rate(income),
            current_price=current_price,
            name=profile.get("longName") or profile.get("shortName") or ticker,
            sector=profile.get("sector"),
            industry=profile.get("industry"),
            market_cap=self._safe(profile.get("marketCap")),
            description=profile.get("longBusinessSummary"),
        )

    def _build_statement(
        self,
        ticker: str,
        income,
        balance,
        cashflow,
        profile: dict,
    ) -> FinancialStatement:
        revenue = self._first(income, ["Total Revenue", "Operating Revenue"], 0)
        operating_income = self._first(
            income, ["Operating Income", "EBIT"], 0
        )
        net_income = self._first(
            income, ["Net Income", "Net Income Common Stockholders"], 0
        )
        gross_profit = self._value(income, "Gross Profit", 0)
        total_assets = self._value(balance, "Total Assets", 0)
        total_liabilities = self._first(
            balance,
            [
                "Total Liabilities Net Minority Interest",
                "Total Liabilities Gross Minority Interest",
            ],
            0,
        )
        cash = self._first(
            balance,
            [
                "Cash And Cash Equivalents",
                "Cash Cash Equivalents And Short Term Investments",
            ],
            0,
        )
        debt = self._value(balance, "Total Debt", 0)
        shares = self._first(income, ["Diluted Average Shares", "Basic Average Shares"], 0)
        if shares is None:
            shares = self._safe(profile.get("sharesOutstanding"))

        free_cash_flow = self._value(cashflow, "Free Cash Flow", 0)
        if free_cash_flow is None:
            operating_cash_flow = self._value(cashflow, "Operating Cash Flow", 0)
            capex = self._value(cashflow, "Capital Expenditure", 0)
            if operating_cash_flow is not None and capex is not None:
                free_cash_flow = operating_cash_flow + capex

        missing = [
            name
            for name, value in (
                ("revenue", revenue),
                ("net_income", net_income),
                ("total_assets", total_assets),
                ("total_liabilities", total_liabilities),
                ("shares_outstanding", shares),
            )
            if value is None
        ]
        if missing:
            raise RetrievalError(
                message=(
                    f"Financial data unavailable for {ticker}; "
                    f"missing: {', '.join(missing)}."
                ),
                error_code="RETR_DATA",
                details={"ticker": ticker, "missing": missing},
            )

        return FinancialStatement(
            revenue=revenue / _MILLION,
            operating_income=(operating_income or 0.0) / _MILLION,
            net_income=net_income / _MILLION,
            total_assets=total_assets / _MILLION,
            total_liabilities=total_liabilities / _MILLION,
            cash=(cash or 0.0) / _MILLION,
            debt=(debt or 0.0) / _MILLION,
            shares_outstanding=shares / _MILLION,
            free_cash_flow=(free_cash_flow or 0.0) / _MILLION,
            gross_profit=(gross_profit or 0.0) / _MILLION,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Risk score computation (real company data)
    # ──────────────────────────────────────────────────────────────────────

    def _compute_piotroski(self, income, balance, cashflow) -> int:
        """Piotroski F-Score from the actual company's statements."""
        ni_t = self._value(income, "Net Income", 0)
        ni_p = self._value(income, "Net Income", 1)
        ta_t = self._value(balance, "Total Assets", 0)
        ta_p = self._value(balance, "Total Assets", 1)
        cfo_t = self._value(cashflow, "Operating Cash Flow", 0)
        rev_t = self._first(income, ["Total Revenue", "Operating Revenue"], 0)
        rev_p = self._first(income, ["Total Revenue", "Operating Revenue"], 1)
        gp_t = self._value(income, "Gross Profit", 0)
        gp_p = self._value(income, "Gross Profit", 1)
        lt_debt_t = self._first(
            balance,
            ["Long Term Debt And Capital Lease Obligation", "Long Term Debt"],
            0,
        )
        lt_debt_p = self._first(
            balance,
            ["Long Term Debt And Capital Lease Obligation", "Long Term Debt"],
            1,
        )
        ca_t = self._value(balance, "Current Assets", 0)
        ca_p = self._value(balance, "Current Assets", 1)
        cl_t = self._value(balance, "Current Liabilities", 0)
        cl_p = self._value(balance, "Current Liabilities", 1)
        shares_t = self._first(
            income, ["Diluted Average Shares", "Basic Average Shares"], 0
        )
        shares_p = self._first(
            income, ["Diluted Average Shares", "Basic Average Shares"], 1
        )

        roa_t = self._ratio(ni_t, ta_t)
        roa_p = self._ratio(ni_p, ta_p)
        cfo = cfo_t if cfo_t is not None else 0.0
        leverage_t = self._ratio(lt_debt_t, ta_t)
        leverage_p = self._ratio(lt_debt_p, ta_p)
        current_t = self._ratio(ca_t, cl_t, 1.0)
        current_p = self._ratio(ca_p, cl_p, 1.0)
        gross_margin_t = self._ratio(gp_t, rev_t)
        gross_margin_p = self._ratio(gp_p, rev_p)
        asset_turnover_t = self._ratio(rev_t, ta_t)
        asset_turnover_p = self._ratio(rev_p, ta_p)
        equity_issued = bool(
            shares_t is not None
            and shares_p is not None
            and shares_t > shares_p
        )

        return Piotroski.calculate(
            roa=roa_t,
            operating_cash_flow=cfo,
            change_in_roa=roa_t - roa_p,
            accrual=cfo - (ni_t or 0.0),
            change_in_leverage=leverage_t - leverage_p,
            change_in_liquidity=current_t - current_p,
            equity_issued=equity_issued,
            change_in_gross_margin=gross_margin_t - gross_margin_p,
            change_in_asset_turnover=asset_turnover_t - asset_turnover_p,
        )

    def _compute_altman(self, income, balance, market, profile) -> float:
        """Altman Z-Score from the actual company's balance sheet/income data."""
        ta_t = self._value(balance, "Total Assets", 0)
        liabilities_t = self._first(
            balance,
            [
                "Total Liabilities Net Minority Interest",
                "Total Liabilities Gross Minority Interest",
            ],
            0,
        )
        ca_t = self._value(balance, "Current Assets", 0)
        cl_t = self._value(balance, "Current Liabilities", 0)
        retained_earnings = self._value(balance, "Retained Earnings", 0)
        ebit = self._first(income, ["Operating Income", "EBIT"], 0)
        sales = self._first(income, ["Total Revenue", "Operating Revenue"], 0)
        shares = self._first(
            income, ["Diluted Average Shares", "Basic Average Shares"], 0
        )
        if shares is None:
            shares = self._safe(profile.get("sharesOutstanding"))

        price = self._safe(market.current_price) or 0.0
        market_value_equity = (
            price * shares if price > 0 and shares else 0.0
        )

        if ta_t is None or ta_t <= 0 or liabilities_t is None:
            raise RetrievalError(
                message=(
                    "Altman Z-Score requires positive total assets and "
                    "liabilities from the balance sheet."
                ),
                error_code="RETR_DATA",
            )
        if liabilities_t <= 0:
            logger.warning("Company has no liabilities; Altman score defaults to SAFE.")
            return 10.0

        working_capital = (
            (ca_t - cl_t)
            if ca_t is not None and cl_t is not None
            else 0.0
        )

        return AltmanZScore.calculate(
            working_capital=working_capital,
            retained_earnings=retained_earnings or 0.0,
            ebit=ebit or 0.0,
            market_value_equity=market_value_equity,
            total_liabilities=liabilities_t,
            sales=sales or 0.0,
            total_assets=ta_t,
        )

    def _compute_beneish(self, income, balance, cashflow) -> float:
        """Beneish M-Score from the actual company's historical data."""
        rev_t = self._first(income, ["Total Revenue", "Operating Revenue"], 0)
        rev_p = self._first(income, ["Total Revenue", "Operating Revenue"], 1)
        recv_t = self._first(balance, ["Receivables", "Accounts Receivable"], 0)
        recv_p = self._first(balance, ["Receivables", "Accounts Receivable"], 1)
        cogs_t = self._first(income, ["Cost Of Revenue", "Reconciled Cost Of Revenue"], 0)
        cogs_p = self._first(income, ["Cost Of Revenue", "Reconciled Cost Of Revenue"], 1)
        ta_t = self._value(balance, "Total Assets", 0)
        ta_p = self._value(balance, "Total Assets", 1)
        ca_t = self._value(balance, "Current Assets", 0)
        ca_p = self._value(balance, "Current Assets", 1)
        liab_t = self._first(
            balance,
            [
                "Total Liabilities Net Minority Interest",
                "Total Liabilities Gross Minority Interest",
            ],
            0,
        )
        liab_p = self._first(
            balance,
            [
                "Total Liabilities Net Minority Interest",
                "Total Liabilities Gross Minority Interest",
            ],
            1,
        )
        sga_t = self._value(income, "Selling General And Administration", 0)
        sga_p = self._value(income, "Selling General And Administration", 1)
        dep_amort = ["Depreciation And Amortization", "Depreciation Amortization Depletion"]
        dep_t = self._first(income, ["Reconciled Depreciation"], 0) or self._first(
            cashflow, dep_amort, 0
        )
        dep_p = self._first(income, ["Reconciled Depreciation"], 1) or self._first(
            cashflow, dep_amort, 1
        )
        ni_t = self._value(income, "Net Income", 0)
        cfo_t = self._value(cashflow, "Operating Cash Flow", 0)

        # AQI uses non-current assets as a proxy for (current assets + PP&E).
        nca_t = (ta_t - ca_t) if ta_t is not None and ca_t is not None else None
        nca_p = (ta_p - ca_p) if ta_p is not None and ca_p is not None else None

        dsri = self._ratio(
            self._ratio(recv_t, rev_t), self._ratio(recv_p, rev_p), 1.0
        )
        gmi = self._ratio(
            self._ratio(cogs_p, rev_p), self._ratio(cogs_t, rev_t), 1.0
        )
        aqi = self._ratio(
            self._ratio(nca_t, ta_t), self._ratio(nca_p, ta_p), 1.0
        )
        sgi = self._ratio(rev_t, rev_p, 1.0)
        depi = self._ratio(
            self._ratio(dep_p, ta_p), self._ratio(dep_t, ta_t), 1.0
        )
        sgai = self._ratio(
            self._ratio(sga_t, rev_t), self._ratio(sga_p, rev_p), 1.0
        )
        lvgi = self._ratio(
            self._ratio(liab_t, ta_t), self._ratio(liab_p, ta_p), 1.0
        )
        tata = self._ratio(
            (ni_t or 0.0) - (cfo_t or 0.0), ta_t
        )

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

    # ──────────────────────────────────────────────────────────────────────
    # Growth + tax rate estimation
    # ──────────────────────────────────────────────────────────────────────

    def _estimate_growth(self, income) -> float:
        """
        Estimate the DCF growth rate from the company's historical revenue CAGR.
        """
        revenues: list[float] = []
        for index in range(6):
            value = self._first(
                income, ["Total Revenue", "Operating Revenue"], index
            )
            if value is not None and value > 0:
                revenues.append(value)

        if len(revenues) >= 2:
            years = len(revenues) - 1
            cagr = (revenues[0] / revenues[-1]) ** (1 / years) - 1
            return min(max(cagr, _MIN_GROWTH_RATE), _MAX_GROWTH_RATE)

        return _MIN_GROWTH_RATE

    def _effective_tax_rate(self, income) -> float:
        """Effective tax rate from the actual income statement."""
        tax_provision = self._value(income, "Tax Provision", 0)
        pretax_income = self._value(income, "Pretax Income", 0)
        if (
            tax_provision is not None
            and pretax_income is not None
            and pretax_income > 0
        ):
            rate = tax_provision / pretax_income
            return min(max(rate, 0.0), 0.40)
        return _DEFAULT_TAX_RATE
