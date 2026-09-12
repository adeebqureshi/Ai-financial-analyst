"""
Demo Fixtures — Synthetic Company Data

This module contains curated deterministic demo data for recognizable companies.
All values are SYNTHETIC/DEMO and clearly labeled as such.
Do not represent fabricated numbers as live market data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Final

from app.enums.exchange import Exchange
from app.financial.models import FinancialStatement
from app.models.company import Company
from app.models.market import MarketData


# ──────────────────────────────────────────────────────────────────────────────
# Demo Company Profiles
# ──────────────────────────────────────────────────────────────────────────────

DEMO_COMPANIES: Final[dict[str, Company]] = {
    "AAPL": Company(
        ticker="AAPL",
        cik="320193",
        name="Apple Inc. [DEMO / SYNTHETIC DATA]",
        exchange=Exchange.NASDAQ,
        sector="Technology",
        industry="Consumer Electronics",
        country="USA",
        currency="USD",
        website="https://www.apple.com",
        market_cap=2_800_000_000_000.0,
    ),
    "MSFT": Company(
        ticker="MSFT",
        cik="789019",
        name="Microsoft Corporation [DEMO / SYNTHETIC DATA]",
        exchange=Exchange.NASDAQ,
        sector="Technology",
        industry="Software Infrastructure",
        country="USA",
        currency="USD",
        website="https://www.microsoft.com",
        market_cap=2_900_000_000_000.0,
    ),
    "GOOGL": Company(
        ticker="GOOGL",
        cik="1652044",
        name="Alphabet Inc. [DEMO / SYNTHETIC DATA]",
        exchange=Exchange.NASDAQ,
        sector="Technology",
        industry="Internet Content & Information",
        country="USA",
        currency="USD",
        website="https://www.alphabet.com",
        market_cap=1_800_000_000_000.0,
    ),
    "AMZN": Company(
        ticker="AMZN",
        cik="1018724",
        name="Amazon.com Inc. [DEMO / SYNTHETIC DATA]",
        exchange=Exchange.NASDAQ,
        sector="Consumer Cyclical",
        industry="Internet Retail",
        country="USA",
        currency="USD",
        website="https://www.amazon.com",
        market_cap=1_500_000_000_000.0,
    ),
    "TSLA": Company(
        ticker="TSLA",
        cik="1318605",
        name="Tesla Inc. [DEMO / SYNTHETIC DATA]",
        exchange=Exchange.NASDAQ,
        sector="Consumer Cyclical",
        industry="Auto Manufacturers",
        country="USA",
        currency="USD",
        website="https://www.tesla.com",
        market_cap=800_000_000_000.0,
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Demo Financial Statements (values in $ millions)
# ──────────────────────────────────────────────────────────────────────────────

DEMO_FINANCIAL_STATEMENTS: Final[dict[str, FinancialStatement]] = {
    "AAPL": FinancialStatement(
        revenue=383_285.0,
        operating_income=114_301.0,
        net_income=96_995.0,
        total_assets=352_755.0,
        total_liabilities=290_437.0,
        cash=62_639.0,
        debt=109_106.0,
        shares_outstanding=15_550.0,
        free_cash_flow=110_543.0,
        gross_profit=169_148.0,
        current_assets=135_405.0,
        current_liabilities=145_308.0,
    ),
    "MSFT": FinancialStatement(
        revenue=211_915.0,
        operating_income=88_523.0,
        net_income=72_361.0,
        total_assets=411_976.0,
        total_liabilities=205_753.0,
        cash=81_054.0,
        debt=47_032.0,
        shares_outstanding=7_430.0,
        free_cash_flow=74_072.0,
        gross_profit=146_048.0,
        current_assets=187_475.0,
        current_liabilities=110_268.0,
    ),
    "GOOGL": FinancialStatement(
        revenue=307_394.0,
        operating_income=84_293.0,
        net_income=73_795.0,
        total_assets=365_264.0,
        total_liabilities=109_120.0,
        cash=110_916.0,
        debt=14_798.0,
        shares_outstanding=12_530.0,
        free_cash_flow=69_505.0,
        gross_profit=172_224.0,
        current_assets=169_126.0,
        current_liabilities=78_006.0,
    ),
    "AMZN": FinancialStatement(
        revenue=574_785.0,
        operating_income=36_852.0,
        net_income=30_425.0,
        total_assets=527_854.0,
        total_liabilities=320_111.0,
        cash=86_820.0,
        debt=84_328.0,
        shares_outstanding=10_350.0,
        free_cash_flow=50_149.0,
        gross_profit=270_051.0,
        current_assets=187_390.0,
        current_liabilities=184_863.0,
    ),
    "TSLA": FinancialStatement(
        revenue=96_773.0,
        operating_income=8_891.0,
        net_income=12_556.0,
        total_assets=106_618.0,
        total_liabilities=50_360.0,
        cash=29_089.0,
        debt=5_748.0,
        shares_outstanding=3_180.0,
        free_cash_flow=4_410.0,
        gross_profit=17_620.0,
        current_assets=57_072.0,
        current_liabilities=34_041.0,
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Demo Market Quotes
# ──────────────────────────────────────────────────────────────────────────────

DEMO_MARKET_QUOTES: Final[dict[str, MarketData]] = {
    "AAPL": MarketData(
        ticker="AAPL",
        exchange=Exchange.NASDAQ,
        current_price=180.0,
        currency="USD",
        market_cap=2_800_000_000_000.0,
        volume=55_000_000,
        beta=1.25,
        pe_ratio=28.5,
        eps=6.24,
        dividend_yield=0.0052,
        week_52_high=198.23,
        week_52_low=124.17,
        provider="demo",
        provider_time=datetime(2024, 12, 31, 16, 0, tzinfo=timezone.utc),
        cached=False,
        stale=False,
    ),
    "MSFT": MarketData(
        ticker="MSFT",
        exchange=Exchange.NASDAQ,
        current_price=390.0,
        currency="USD",
        market_cap=2_900_000_000_000.0,
        volume=22_000_000,
        beta=0.92,
        pe_ratio=34.2,
        eps=9.74,
        dividend_yield=0.0071,
        week_52_high=430.82,
        week_52_low=309.45,
        provider="demo",
        provider_time=datetime(2024, 12, 31, 16, 0, tzinfo=timezone.utc),
        cached=False,
        stale=False,
    ),
    "GOOGL": MarketData(
        ticker="GOOGL",
        exchange=Exchange.NASDAQ,
        current_price=142.0,
        currency="USD",
        market_cap=1_800_000_000_000.0,
        volume=28_000_000,
        beta=1.05,
        pe_ratio=24.3,
        eps=5.84,
        dividend_yield=0.0,
        week_52_high=153.78,
        week_52_low=121.46,
        provider="demo",
        provider_time=datetime(2024, 12, 31, 16, 0, tzinfo=timezone.utc),
        cached=False,
        stale=False,
    ),
    "AMZN": MarketData(
        ticker="AMZN",
        exchange=Exchange.NASDAQ,
        current_price=145.0,
        currency="USD",
        market_cap=1_500_000_000_000.0,
        volume=35_000_000,
        beta=1.15,
        pe_ratio=48.9,
        eps=2.94,
        dividend_yield=0.0,
        week_52_high=189.77,
        week_52_low=118.35,
        provider="demo",
        provider_time=datetime(2024, 12, 31, 16, 0, tzinfo=timezone.utc),
        cached=False,
        stale=False,
    ),
    "TSLA": MarketData(
        ticker="TSLA",
        exchange=Exchange.NASDAQ,
        current_price=250.0,
        currency="USD",
        market_cap=800_000_000_000.0,
        volume=85_000_000,
        beta=2.15,
        pe_ratio=63.5,
        eps=3.95,
        dividend_yield=0.0,
        week_52_high=299.29,
        week_52_low=138.80,
        provider="demo",
        provider_time=datetime(2024, 12, 31, 16, 0, tzinfo=timezone.utc),
        cached=False,
        stale=False,
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Demo Risk Scores (computed from demo financial data)
# ──────────────────────────────────────────────────────────────────────────────

DEMO_RISK_SCORES: Final[dict[str, dict[str, float | int]]] = {
    "AAPL": {
        "piotroski_score": 8,
        "altman_score": 4.2,
        "beneish_score": -2.1,
    },
    "MSFT": {
        "piotroski_score": 9,
        "altman_score": 5.8,
        "beneish_score": -2.8,
    },
    "GOOGL": {
        "piotroski_score": 8,
        "altman_score": 4.9,
        "beneish_score": -2.3,
    },
    "AMZN": {
        "piotroski_score": 7,
        "altman_score": 3.1,
        "beneish_score": -1.8,
    },
    "TSLA": {
        "piotroski_score": 6,
        "altman_score": 2.9,
        "beneish_score": -1.2,
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Demo Growth Rates (historical revenue CAGR estimates)
# ──────────────────────────────────────────────────────────────────────────────

DEMO_GROWTH_RATES: Final[dict[str, float]] = {
    "AAPL": 0.085,
    "MSFT": 0.12,
    "GOOGL": 0.15,
    "AMZN": 0.18,
    "TSLA": 0.25,
}


# ──────────────────────────────────────────────────────────────────────────────
# Demo Tax Rates (effective tax rates from demo income statements)
# ──────────────────────────────────────────────────────────────────────────────

DEMO_TAX_RATES: Final[dict[str, float]] = {
    "AAPL": 0.16,
    "MSFT": 0.19,
    "GOOGL": 0.17,
    "AMZN": 0.14,
    "TSLA": 0.09,
}


# ──────────────────────────────────────────────────────────────────────────────
# Demo Company Descriptions
# ──────────────────────────────────────────────────────────────────────────────

DEMO_DESCRIPTIONS: Final[dict[str, str]] = {
    "AAPL": (
        "Apple Inc. designs, manufactures, and markets smartphones, personal "
        "computers, tablets, wearables, and accessories worldwide. The company "
        "also provides related services including Apple Music, iCloud, Apple Pay, "
        "and the App Store. [DEMO / SYNTHETIC DATA]"
    ),
    "MSFT": (
        "Microsoft Corporation develops, licenses, and supports software, services, "
        "devices, and solutions worldwide. Its segments include Productivity and "
        "Business Processes, Intelligent Cloud, and More Personal Computing. "
        "[DEMO / SYNTHETIC DATA]"
    ),
    "GOOGL": (
        "Alphabet Inc. provides online advertising services, cloud computing, "
        "software, and hardware products. Google Services includes Search, Ads, "
        "YouTube, Android, Chrome, and Maps. Google Cloud provides infrastructure "
        "and platform services. [DEMO / SYNTHETIC DATA]"
    ),
    "AMZN": (
        "Amazon.com Inc. engages in the retail sale of consumer products and "
        "subscriptions through online and physical stores. AWS provides cloud "
        "computing services. The company also manufactures and sells electronic "
        "devices including Kindle, Fire tablets, and Echo devices. "
        "[DEMO / SYNTHETIC DATA]"
    ),
    "TSLA": (
        "Tesla Inc. designs, develops, manufactures, and sells electric vehicles "
        "and energy generation and storage systems. The company also provides "
        "automotive regulatory credits and sells solar energy products. "
        "[DEMO / SYNTHETIC DATA]"
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Demo Available Tickers
# ──────────────────────────────────────────────────────────────────────────────

DEMO_TICKERS: Final[list[str]] = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]


def is_demo_ticker(ticker: str) -> bool:
    """Check if a ticker is available in demo mode."""
    return ticker.upper() in DEMO_TICKERS


def get_demo_company(ticker: str) -> Company:
    """Get demo company profile by ticker."""
    return DEMO_COMPANIES[ticker.upper()]


def get_demo_financial_statement(ticker: str) -> FinancialStatement:
    """Get demo financial statement by ticker."""
    return DEMO_FINANCIAL_STATEMENTS[ticker.upper()]


def get_demo_market_data(ticker: str) -> MarketData:
    """Get demo market data by ticker."""
    return DEMO_MARKET_QUOTES[ticker.upper()]


def get_demo_risk_scores(ticker: str) -> dict[str, float | int]:
    """Get demo risk scores by ticker."""
    return DEMO_RISK_SCORES[ticker.upper()]


def get_demo_growth_rate(ticker: str) -> float:
    """Get demo growth rate by ticker."""
    return DEMO_GROWTH_RATES[ticker.upper()]


def get_demo_tax_rate(ticker: str) -> float:
    """Get demo tax rate by ticker."""
    return DEMO_TAX_RATES[ticker.upper()]


def get_demo_description(ticker: str) -> str:
    """Get demo company description by ticker."""
    return DEMO_DESCRIPTIONS[ticker.upper()]