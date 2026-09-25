"""Demo integrations loaded only when explicitly selected.

Exports are resolved lazily so importing this package cannot import the demo
market provider as a production-runtime side effect.
"""
from __future__ import annotations

from importlib import import_module

__all__ = [
    "DemoMarketProvider",
    "DemoFinancialDataService",
    "DemoSECService",
    "create_demo_vector_store",
    "build_demo_retrieval_context",
    "DEMO_FILING_CHUNKS",
]


def __getattr__(name: str):
    if name == "DemoMarketProvider":
        return getattr(
            import_module("app.demo.providers.demo_market_provider"),
            name,
        )
    if name in {"DemoFinancialDataService", "DemoSECService"}:
        module = {
            "DemoFinancialDataService": "app.demo.services.demo_financial_data",
            "DemoSECService": "app.demo.services.demo_sec_service",
        }[name]
        return getattr(import_module(module), name)
    if name in {
        "create_demo_vector_store",
        "build_demo_retrieval_context",
        "DEMO_FILING_CHUNKS",
    }:
        return getattr(import_module("app.demo.fixtures.rag_fixtures"), name)
    raise AttributeError(name)