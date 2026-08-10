from types import SimpleNamespace

from app.agents.tools import ToolRegistry
from app.financial.models import FinancialStatement


def _statement():
    return FinancialStatement(
        revenue=394_328.0,
        operating_income=114_301.0,
        net_income=96_995.0,
        total_assets=352_583.0,
        total_liabilities=279_486.0,
        cash=30_545.0,
        debt=111_088.0,
        shares_outstanding=15_431.0,
        free_cash_flow=99_584.0,
    )


class FakeFinancials:
    """Mimics FinancialDataService.load() with per-ticker data."""

    def __init__(self, by_ticker: dict) -> None:
        self._by_ticker = by_ticker

    def load(self, ticker: str):
        ticker = ticker.upper()
        if ticker not in self._by_ticker:
            raise ValueError(f"no data for {ticker}")
        return self._by_ticker[ticker]


class FakeMarket:
    def __init__(self, prices: dict) -> None:
        self._prices = prices

    def get_market_data(self, ticker: str):
        ticker = ticker.upper()
        return SimpleNamespace(
            ticker=ticker,
            exchange=SimpleNamespace(value="NASDAQ"),
            current_price=self._prices[ticker],
            currency="USD",
            market_cap=1_000_000_000_000,
            volume=50_000_000,
            beta=1.2,
            pe_ratio=25.0,
            eps=6.0,
            dividend_yield=0.005,
            week_52_high=250.0,
            week_52_low=150.0,
        )


class FakeCompany:
    def __init__(self, names: dict) -> None:
        self._names = names

    def get_company(self, ticker: str):
        return SimpleNamespace(
            ticker=ticker.upper(),
            name=self._names[ticker.upper()],
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=1_000_000_000_000,
            description="A company.",
        )


class FakeDocuments:
    def __init__(self) -> None:
        self.queries = []

    def retrieve(self, query, limit=5, document_id=None):
        self.queries.append((query, limit, document_id))
        return SimpleNamespace(
            chunks=[
                SimpleNamespace(
                    id="doc1:0",
                    chunk_id="doc1:0",
                    text="Apple supply chain concentration risk.",
                    score=0.91,
                    document_id="doc1",
                    filename="Apple 10-K.pdf",
                    page=42,
                    ticker="Apple",
                    section="Risk Factors",
                    source="Apple 10-K.pdf:page-42",
                    filing_type="10-K",
                ),
                SimpleNamespace(
                    id="doc2:0",
                    chunk_id="doc2:0",
                    text="Microsoft Azure growth.",
                    score=0.87,
                    document_id="doc2",
                    filename="Microsoft 10-K.pdf",
                    page=12,
                    ticker="Microsoft",
                    section="Business",
                    source="Microsoft 10-K.pdf:page-12",
                    filing_type="10-K",
                ),
            ],
            retrieval_time_ms=5.0,
        )


def _company_data(ticker: str, price: float) -> SimpleNamespace:
    return SimpleNamespace(
        ticker=ticker,
        name={0: "Apple", 1: "Microsoft"}[0] if ticker == "AAPL" else "Microsoft",
        sector="Technology",
        industry="Software",
        market_cap=price * 15_431,
        description="Company description.",
        current_price=price,
        growth_rate=0.08,
        beta=1.2,
        tax_rate=0.21,
        piotroski_score=8,
        altman_score=3.5,
        beneish_score=-2.4,
        statement=_statement(),
    )


def _registry(**overrides) -> ToolRegistry:
    financials = FakeFinancials(
        {
            "AAPL": _company_data("AAPL", 220.0),
            "MSFT": _company_data("MSFT", 430.0),
        }
    )
    market = FakeMarket({"AAPL": 220.0, "MSFT": 430.0})
    company = FakeCompany({"AAPL": "Apple Inc.", "MSFT": "Microsoft Corp."})
    documents = FakeDocuments()

    return ToolRegistry(
        financials=financials,
        market=market,
        company=company,
        documents=documents,
        **overrides,
    )


def test_market_data_returns_structured_price():
    registry = _registry()

    result = registry.execute("get_market_data", {"ticker": "aapl"})

    assert result.status == "done"

    assert result.result["ticker"] == "AAPL"

    assert result.result["current_price"] == 220.0


def test_financials_are_ticker_isolated():
    registry = _registry()

    aapl = registry.execute("get_financials", {"ticker": "AAPL"}).result

    msft = registry.execute("get_financials", {"ticker": "MSFT"}).result

    assert aapl["ticker"] == "AAPL"

    assert msft["ticker"] == "MSFT"

    assert msft["current_price"] == 430.0


def test_valuation_returns_intrinsic_value_and_upside():
    registry = _registry()

    result = registry.execute("calculate_valuation", {"ticker": "AAPL"})

    assert result.status == "done"

    payload = result.result

    assert payload["ticker"] == "AAPL"

    assert "intrinsic_value" in payload

    assert "upside" in payload

    assert "current_price" in payload


def test_search_documents_preserves_metadata_and_filters_by_ticker():
    registry = _registry()

    result = registry.execute(
        "search_documents",
        {"query": "supply chain", "ticker": "AAPL"},
    )

    assert result.status == "done"

    assert result.result["ticker_filtered"] is True

    assert result.result["total"] == 1

    chunk = result.result["chunks"][0]

    assert chunk["document_id"] == "doc1"

    assert chunk["filename"] == "Apple 10-K.pdf"

    assert chunk["page"] == 42

    assert chunk["score"] == 0.91


def test_search_documents_never_leaks_other_company():
    registry = _registry()

    result = registry.execute(
        "search_documents",
        {"query": "growth", "ticker": "MSFT"},
    )

    filenames = [chunk["filename"] for chunk in result.result["chunks"]]

    assert filenames == ["Microsoft 10-K.pdf"]


def test_unknown_tool_returns_error_result():
    registry = _registry()

    result = registry.execute("does_not_exist", {})

    assert result.status == "error"

    assert result.result is None


def test_failed_tool_does_not_raise():
    registry = _registry()

    result = registry.execute("get_financials", {"ticker": "NOPE"})

    assert result.status == "error"

    assert result.result is None

    assert result.error
