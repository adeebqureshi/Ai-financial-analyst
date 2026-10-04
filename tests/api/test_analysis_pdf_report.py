"""Tests for the analysis PDF report renderer and its endpoint.

Background
----------
``POST /analysis/pdf-report`` renders the analysis the workspace has *already*
computed into a downloadable document. Two properties matter most and are
pinned here:

1. The document is a real, openable PDF built from the supplied payload -- not
   a screenshot, an HTML dump or a set of hardcoded numbers.
2. Nothing is recomputed. The endpoint takes the finished result from the
   client, so downloading a report cannot disagree with the analysis on screen
   and cannot trigger a second run of the financial pipeline.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.main import app
from app.services.pdf_report_service import (
    AnalysisPdfPayload,
    PdfReportError,
    build_filename,
    render_analysis_pdf,
)


class MockUser:
    id = "test_user_123"


@pytest.fixture()
def auth_client():
    app.dependency_overrides[get_current_user] = lambda: MockUser()
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def sample_payload(**overrides) -> AnalysisPdfPayload:
    base = dict(
        ticker="NVDA",
        company={
            "ticker": "NVDA",
            "name": "NVIDIA Corporation",
            "sector": "Technology",
            "industry": "Semiconductors",
            "market_cap": 4.29e12,
            "description": "Designs GPUs and accelerated computing platforms.",
        },
        market={
            "ticker": "NVDA",
            "exchange": "NASDAQ",
            "current_price": 175.43,
            "currency": "USD",
            "market_cap": 4.29e12,
            "volume": 51_234_000,
            "beta": 2.11,
            "pe_ratio": 45.6,
            "eps": 3.85,
            "dividend_yield": 0.0002,
            "week_52_high": 180.42,
            "week_52_low": 86.62,
            "provider": "stooq",
            "as_of": "2026-10-03T20:00:00Z",
        },
        statement={
            "revenue": 3.83e11,
            "operating_income": 1.83e11,
            "net_income": 9.7e10,
            "total_assets": 3.52e11,
            "total_liabilities": 2.9e11,
            "cash": 7.27e10,
            "debt": 8.46e9,
            "shares_outstanding": 2.45e10,
            "free_cash_flow": 1.1e11,
        },
        valuation={
            "intrinsic_value": 142.30,
            "upside": -18.87,
            "recommendation": "HOLD",
            "current_price": 175.43,
            "discount_rate": 0.105,
        },
        health={
            "score": 85,
            "rating": "Strong",
            "piotroski_score": 8,
            "altman_score": 3.52,
            "beneish_score": -1.86,
        },
        recommendation="HOLD",
        risk={
            "health_score": 85,
            "health_rating": "Strong",
            "piotroski": {"interpretation": "Strong operating momentum"},
            "altman": {"zone": "Safe zone"},
            "beneish": {"flag": "No manipulation detected"},
            "risk_level": "MEDIUM",
        },
    )
    base.update(overrides)
    return AnalysisPdfPayload(**base)


def pdf_text(document: bytes) -> str:
    import pymupdf

    with pymupdf.open(stream=document, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


# ---------------------------------------------------------------- renderer


class TestRenderer:
    def test_produces_a_real_openable_pdf(self):
        document = render_analysis_pdf(sample_payload())

        assert document.startswith(b"%PDF-")
        assert len(document) > 1000

        import pymupdf

        with pymupdf.open(stream=document, filetype="pdf") as doc:
            assert doc.page_count >= 1
            # A truncated or malformed file has to be repaired to be read.
            assert doc.is_repaired is False
            assert not doc.needs_pass

    def test_contains_the_real_company_and_ticker(self):
        text = pdf_text(render_analysis_pdf(sample_payload()))

        assert "NVIDIA Corporation" in text
        assert "NVDA" in text

    def test_contains_real_analysis_values(self):
        text = pdf_text(render_analysis_pdf(sample_payload()))

        # Valuation, health and statement figures must survive into the PDF.
        assert "$142.30" in text
        assert "$175.43" in text
        assert "-18.87%" in text
        assert "HOLD" in text
        assert "$383.00B" in text
        assert "3.52" in text
        assert "MEDIUM" in text

    def test_includes_every_expected_section(self):
        text = pdf_text(render_analysis_pdf(sample_payload()))

        for heading in (
            "Executive summary",
            "Company overview",
            "Market data",
            "Valuation",
            "Financial health",
            "Financial statements",
            "Risk analysis",
            "AI insights",
            "Data sources",
        ):
            assert heading in text, heading

    def test_has_page_numbers_and_a_generation_timestamp(self):
        document = render_analysis_pdf(sample_payload())
        text = pdf_text(document)

        assert "Page 1 of" in text
        assert "Generated:" in text

    def test_missing_fields_are_marked_not_invented(self):
        payload = sample_payload(
            market={
                "ticker": "ZZZZ",
                "exchange": None,
                "currency": "USD",
                "current_price": None,
                "market_cap": None,
                "beta": None,
                "pe_ratio": None,
                "eps": None,
                "dividend_yield": None,
                "week_52_high": None,
                "week_52_low": None,
                "volume": None,
            },
            # No upside either, so the status line has to say so honestly.
            valuation={
                "intrinsic_value": None,
                "upside": None,
                "recommendation": None,
                "current_price": None,
                "discount_rate": None,
            },
            risk=None,
        )
        text = pdf_text(render_analysis_pdf(payload))

        # Absent data must read as unavailable, never as a fabricated zero.
        assert "Not available" in text
        assert "Trading in line with the modelled intrinsic value." in text

    def test_escapes_provider_supplied_text(self):
        payload = sample_payload(
            company={
                "ticker": "X",
                "name": "Acme <script>alert(1)</script> & Co",
                "sector": "Tech",
                "industry": None,
                "market_cap": None,
                "description": "Uses & and <angles>",
            }
        )
        text = pdf_text(render_analysis_pdf(payload))

        # Entities are decoded for display...
        assert "&amp;" not in text
        assert "& Co" in text
        assert "Uses & and <angles>" in text
        # ...and the tags survive as inert literal text, which is only true if
        # they were escaped. An unescaped <script> would have been swallowed by
        # the HTML parser instead of printed.
        assert "<script>alert(1)</script>" in text

    def test_rejects_a_payload_without_a_ticker(self):
        with pytest.raises(PdfReportError):
            render_analysis_pdf(sample_payload(ticker=""))


class TestFilename:
    def test_uses_the_expected_pattern(self):
        assert build_filename("NVDA") == "NVDA_Financial_Analysis_Report.pdf"
        assert build_filename("AAPL") == "AAPL_Financial_Analysis_Report.pdf"

    def test_uppercases_and_sanitises(self):
        assert build_filename("aapl") == "AAPL_Financial_Analysis_Report.pdf"

    @pytest.mark.parametrize(
        "hostile",
        ["../../etc/passwd", "NVDA/../X", "NV DA", "..", "///", "N.V:D|A"],
    )
    def test_strips_characters_that_are_illegal_in_a_path(self, hostile):
        name = build_filename(hostile)

        assert "/" not in name
        assert "\\" not in name
        assert ".." not in name
        assert ":" not in name
        assert name.endswith("_Financial_Analysis_Report.pdf")

    def test_always_produces_a_usable_name(self):
        assert build_filename("").endswith("_Financial_Analysis_Report.pdf")


# ---------------------------------------------------------------- endpoint


class TestEndpoint:
    def _body(self, **overrides):
        payload = sample_payload()
        body = {
            "ticker": payload.ticker,
            "company": payload.company,
            "market": payload.market,
            "statement": payload.statement,
            "valuation": payload.valuation,
            "health": payload.health,
            "recommendation": payload.recommendation,
            "risk": payload.risk,
        }
        body.update(overrides)
        return body

    def test_rejects_an_unauthenticated_request(self):
        """
        The PDF route sits behind the same ``get_current_user`` guard as every
        other data route.

        Auth is disabled in the test environment, so it is switched on for this
        case to prove the guard actually rejects an anonymous caller.
        """
        from app.auth.dependencies import get_auth_settings
        from app.core.config import get_settings

        enabled = get_settings().model_copy(update={"auth_enabled": True})
        app.dependency_overrides[get_auth_settings] = lambda: enabled

        try:
            with TestClient(app) as client:
                response = client.post("/analysis/pdf-report", json=self._body())
        finally:
            app.dependency_overrides.pop(get_auth_settings, None)

        assert response.status_code in (401, 403)

    def test_returns_pdf_with_a_download_filename(self, auth_client):
        response = auth_client.post("/analysis/pdf-report", json=self._body())

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/pdf")
        assert "attachment" in response.headers["content-disposition"]
        assert "NVDA_Financial_Analysis_Report.pdf" in response.headers[
            "content-disposition"
        ]
        assert response.content.startswith(b"%PDF-")

    def test_refuses_a_request_without_company_data(self, auth_client):
        response = auth_client.post(
            "/analysis/pdf-report", json=self._body(company={})
        )

        assert response.status_code == 422

    def test_refuses_a_request_without_a_ticker(self, auth_client):
        response = auth_client.post("/analysis/pdf-report", json=self._body(ticker=""))

        assert response.status_code == 422

    def test_does_not_call_the_analysis_pipeline(self, auth_client, monkeypatch):
        """
        The whole point of the endpoint: producing a document must never re-run
        market data, the valuation model or an LLM.

        Proven by making every service the analysis pipeline would need explode
        if it were touched.
        """
        import app.api.dependencies.services as services

        def explode(*args, **kwargs):  # pragma: no cover - must not run
            raise AssertionError("the PDF route must not analyse anything")

        for name in (
            "get_analysis_service",
            "get_risk_service",
            "get_valuation_service",
            "get_report_service",
        ):
            monkeypatch.setattr(services, name, explode)

        response = auth_client.post("/analysis/pdf-report", json=self._body())

        assert response.status_code == 200
        assert response.content.startswith(b"%PDF-")