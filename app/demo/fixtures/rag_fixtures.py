"""
Demo RAG Fixtures — Synthetic Filing Content for Vector Search

This module provides deterministic synthetic filing text chunks and embeddings
for demonstrating RAG/search functionality without external Qdrant.
"""

from __future__ import annotations

from app.rag.embedding import Embedding
from app.rag.memory_store import MemoryVectorStore


# ──────────────────────────────────────────────────────────────────────────────
# Synthetic Filing Text Chunks
# ──────────────────────────────────────────────────────────────────────────────

# Each chunk represents a section from a synthetic SEC filing
# All content is clearly labeled as DEMO / SYNTHETIC DATA

DEMO_FILING_CHUNKS: dict[str, list[dict[str, str]]] = {
    "AAPL": [
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Apple Inc. 2024 Form 10-K — Item 1. Business. "
                "Apple designs, manufactures, and markets smartphones, personal computers, "
                "tablets, wearables, and accessories worldwide. The Company's products "
                "include iPhone, Mac, iPad, AirPods, Apple TV, Apple Watch, Beats products, "
                "HomePod, iPod touch, and accessories. The Company also provides related "
                "services including Apple Music, iCloud, Apple Pay, Apple Card, Apple News+, "
                "Apple Fitness+, Apple Arcade, Apple TV+, and the App Store. Net sales for "
                "fiscal year 2024 were $383.3 billion, an increase of 2% compared to 2023."
            ),
            "section": "Item 1. Business",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Apple Inc. 2024 Form 10-K — Item 1A. Risk Factors. "
                "Global economic conditions, including inflation, rising interest rates, and "
                "currency fluctuations, could materially adversely affect demand for the "
                "Company's products and services. The Company faces intense competition in "
                "all markets for its products and services. Supply chain disruptions, "
                "including shortages of semiconductor components, could delay or prevent "
                "product shipments."
            ),
            "section": "Item 1A. Risk Factors",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Apple Inc. 2024 Form 10-K — Item 7. Management's "
                "Discussion and Analysis. The Company generated $110.5 billion in free cash "
                "flow during fiscal 2024. Cash and marketable securities were $62.6 billion "
                "at September 28, 2024. Total debt was $109.1 billion. The Company returned "
                "over $90 billion to shareholders through dividends and share repurchases in "
                "fiscal 2024. Gross margin was 44.1% in fiscal 2024, up from 43.6% in 2023."
            ),
            "section": "Item 7. MD&A",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Apple Inc. 2024 Form 10-K — Item 8. Financial "
                "Statements. Revenue by segment: iPhone $200.6B, Services $96.2B, Mac $29.9B, "
                "Wearables $37.0B, iPad $28.3B. Geographic revenue: Americas $167.0B, "
                "Europe $94.3B, Greater China $73.1B, Japan $25.7B, Rest of Asia Pacific "
                "$23.2B. Total assets $352.8B, total liabilities $290.4B, shareholders' "
                "equity $62.3B at September 28, 2024."
            ),
            "section": "Item 8. Financial Statements",
            "filing_type": "10-K",
        },
    ],
    "MSFT": [
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Microsoft Corporation 2024 Form 10-K — Item 1. "
                "Business. Microsoft develops, licenses, and supports software, services, "
                "devices, and solutions worldwide. The Company operates through three "
                "segments: Productivity and Business Processes (Office, LinkedIn, Dynamics), "
                "Intelligent Cloud (Azure, SQL Server, Windows Server, GitHub), and More "
                "Personal Computing (Windows, Devices, Gaming, Search). Revenue for fiscal "
                "year 2024 was $211.9 billion, an increase of 16% compared to 2023."
            ),
            "section": "Item 1. Business",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Microsoft Corporation 2024 Form 10-K — Item 1A. "
                "Risk Factors. The Company faces intense competition across all segments, "
                "including from well-funded competitors with significant market share. "
                "Cybersecurity threats and data breaches could result in significant "
                "financial and reputational damage. Regulatory scrutiny, particularly in "
                "the EU and US, could limit business practices or require product changes."
            ),
            "section": "Item 1A. Risk Factors",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Microsoft Corporation 2024 Form 10-K — Item 7. "
                "Management's Discussion and Analysis. The Company generated $74.1 billion "
                "in free cash flow during fiscal 2024. Cash and short-term investments were "
                "$81.1 billion at June 30, 2024. Total debt was $47.0 billion. Commercial "
                "cloud revenue surpassed $135 billion, up 23% year-over-year. Azure revenue "
                "growth was 29% in constant currency. Operating margin was 41.8%."
            ),
            "section": "Item 7. MD&A",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Microsoft Corporation 2024 Form 10-K — Item 8. "
                "Financial Statements. Revenue by segment: Productivity $69.3B, Intelligent "
                "Cloud $105.4B, More Personal Computing $59.7B. Geographic revenue: United "
                "States $108.7B, International $103.2B. Total assets $412.0B, total "
                "liabilities $205.8B, shareholders' equity $206.2B at June 30, 2024."
            ),
            "section": "Item 8. Financial Statements",
            "filing_type": "10-K",
        },
    ],
    "GOOGL": [
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Alphabet Inc. 2023 Form 10-K — Item 1. Business. "
                "Alphabet provides online advertising services, cloud computing, software, "
                "and hardware products. Google Services includes Search, YouTube, Android, "
                "Chrome, Maps, Play, and hardware (Pixel, Nest, Fitbit). Google Cloud "
                "provides infrastructure, platform, and workspace services. Other Bets "
                "include Waymo, Verily, and other early-stage investments. Revenue for 2023 "
                "was $307.4 billion, an increase of 9% compared to 2022."
            ),
            "section": "Item 1. Business",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Alphabet Inc. 2023 Form 10-K — Item 1A. Risk "
                "Factors. The Company generates a substantial majority of revenue from "
                "advertising, making it vulnerable to economic downturns. Regulatory "
                "investigations and litigation, including antitrust cases in the US and EU, "
                "could result in significant fines or required business changes. AI "
                "competition from OpenAI, Microsoft, and others could erode search dominance."
            ),
            "section": "Item 1A. Risk Factors",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Alphabet Inc. 2023 Form 10-K — Item 7. Management's "
                "Discussion and Analysis. The Company generated $69.5 billion in free cash "
                "flow during 2023. Cash and marketable securities were $110.9 billion at "
                "December 31, 2023. Total debt was $14.8 billion. Google Cloud revenue was "
                "$33.1 billion, growing 26% year-over-year. YouTube advertising revenue was "
                "$31.5 billion. Operating margin was 27.4%."
            ),
            "section": "Item 7. MD&A",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Alphabet Inc. 2023 Form 10-K — Item 8. Financial "
                "Statements. Revenue by segment: Google Services $272.8B, Google Cloud $33.1B, "
                "Other Bets $1.5B. Geographic revenue: United States $157.3B, EMEA $84.5B, "
                "APAC $49.8B, Other Americas $15.8B. Total assets $365.3B, total liabilities "
                "$109.1B, shareholders' equity $256.2B at December 31, 2023."
            ),
            "section": "Item 8. Financial Statements",
            "filing_type": "10-K",
        },
    ],
    "AMZN": [
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Amazon.com Inc. 2023 Form 10-K — Item 1. Business. "
                "Amazon engages in retail sale of consumer products through online and "
                "physical stores. AWS provides cloud computing services including compute, "
                "storage, database, analytics, and AI/ML. Amazon also manufactures and sells "
                "electronic devices (Kindle, Fire tablets, Fire TV, Echo, Ring) and produces "
                "digital content. Revenue for 2023 was $574.8 billion, an increase of 12% "
                "compared to 2022."
            ),
            "section": "Item 1. Business",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Amazon.com Inc. 2023 Form 10-K — Item 1A. Risk "
                "Factors. The Company faces intense competition in e-commerce, cloud "
                "computing, and digital content. Labor costs, unionization efforts, and "
                "regulatory scrutiny (antitrust, worker safety) could increase expenses. "
                "AWS growth depends on enterprise adoption; competition from Microsoft Azure "
                "and Google Cloud is significant. Thin retail margins limit profitability."
            ),
            "section": "Item 1A. Risk Factors",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Amazon.com Inc. 2023 Form 10-K — Item 7. Management's "
                "Discussion and Analysis. The Company generated $50.1 billion in free cash "
                "flow during 2023. Cash and marketable securities were $86.8 billion at "
                "December 31, 2023. Total debt was $84.3 billion. AWS revenue was $90.8B "
                "(operating margin 30.5%). North America retail revenue was $352.8B, "
                "International retail revenue was $131.2B. Operating margin was 6.4%."
            ),
            "section": "Item 7. MD&A",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Amazon.com Inc. 2023 Form 10-K — Item 8. Financial "
                "Statements. Revenue by segment: North America $352.8B, International $131.2B, "
                "AWS $90.8B. Geographic revenue: United States $381.6B, International $193.2B. "
                "Total assets $527.9B, total liabilities $320.1B, shareholders' equity $207.7B "
                "at December 31, 2023."
            ),
            "section": "Item 8. Financial Statements",
            "filing_type": "10-K",
        },
    ],
    "TSLA": [
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Tesla Inc. 2023 Form 10-K — Item 1. Business. "
                "Tesla designs, develops, manufactures, and sells electric vehicles and "
                "energy generation and storage systems. Vehicle models include Model S, 3, X, "
                "Y, Cybertruck, and Semi. Energy products include Powerwall, Powerpack, "
                "Megapack, and Solar Roof. Revenue for 2023 was $96.8 billion, an increase "
                "of 19% compared to 2022. Vehicle deliveries were 1.81 million units."
            ),
            "section": "Item 1. Business",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Tesla Inc. 2023 Form 10-K — Item 1A. Risk Factors. "
                "The Company faces intense competition in EVs from traditional automakers "
                "(Ford, GM, VW, BYD) and new entrants. Elon Musk's role and public "
                "statements create concentration and reputational risk. Battery supply chain "
                "constraints, raw material costs (lithium, cobalt), and regulatory changes "
                "(EV tax credits, emissions standards) could materially affect results."
            ),
            "section": "Item 1A. Risk Factors",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Tesla Inc. 2023 Form 10-K — Item 7. Management's "
                "Discussion and Analysis. The Company generated $4.4 billion in free cash "
                "flow during 2023. Cash and marketable securities were $29.1 billion at "
                "December 31, 2023. Total debt was $5.7 billion. Automotive revenue was "
                "$82.4B with 18.2% gross margin. Energy revenue was $6.0B with 14.3% gross "
                "margin. Operating margin was 9.2%."
            ),
            "section": "Item 7. MD&A",
            "filing_type": "10-K",
        },
        {
            "text": (
                "[DEMO / SYNTHETIC DATA] Tesla Inc. 2023 Form 10-K — Item 8. Financial "
                "Statements. Revenue by segment: Automotive $82.4B, Energy Generation and "
                "Storage $6.0B, Services and Other $8.4B. Geographic revenue: United States "
                "$45.2B, China $21.8B, Other $29.8B. Total assets $106.6B, total liabilities "
                "$50.4B, shareholders' equity $56.3B at December 31, 2023."
            ),
            "section": "Item 8. Financial Statements",
            "filing_type": "10-K",
        },
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# Demo Vector Store Initialization
# ──────────────────────────────────────────────────────────────────────────────

def create_demo_vector_store() -> MemoryVectorStore:
    """
    Create a pre-populated in-memory vector store with demo filing chunks.

    Uses deterministic local embeddings (via the existing fallback mechanism)
    so no external embedding API is required.

    Returns:
        A MemoryVectorStore populated with demo filing embeddings.
    """
    store = MemoryVectorStore()

    # Import here to avoid circular imports
    from app.embeddings.embedding_service import _fallback_vector, EmbeddingService

    embedder = EmbeddingService()

    # Add all demo chunks to the vector store
    for ticker, chunks in DEMO_FILING_CHUNKS.items():
        for i, chunk_data in enumerate(chunks):
            text = chunk_data["text"]
            vector = embedder.embed_text(text)

            embedding = Embedding(
                text=text,
                vector=vector,
                metadata={
                    "ticker": ticker,
                    "filing_type": chunk_data["filing_type"],
                    "section": chunk_data["section"],
                    "source": f"demo_{ticker}_{chunk_data['filing_type']}_{i}",
                    "chunk_id": f"demo_{ticker}_{i:06d}",
                },
            )
            store.add(embedding)

    return store


# ──────────────────────────────────────────────────────────────────────────────
# Demo Retrieval Context Builder
# ──────────────────────────────────────────────────────────────────────────────

from app.retrieval.models import RetrievalChunk, RetrievalContext


def build_demo_retrieval_context(
    query: str,
    ticker: str | None = None,
    limit: int = 5,
) -> RetrievalContext:
    """
    Build a deterministic retrieval context for demo queries.

    This bypasses the vector store and directly returns relevant demo chunks
    based on keyword matching, ensuring deterministic results.

    Args:
        query: The search query.
        ticker: Optional ticker to scope results.
        limit: Maximum number of chunks to return.

    Returns:
        A RetrievalContext with relevant demo chunks.
    """
    import time

    start = time.perf_counter()

    query_lower = query.lower()
    scored_chunks: list[tuple[float, dict]] = []

    # Score chunks by keyword overlap
    for tkr, chunks in DEMO_FILING_CHUNKS.items():
        if ticker and tkr != ticker.upper():
            continue
        for i, chunk in enumerate(chunks):
            text_lower = chunk["text"].lower()
            # Simple keyword scoring
            score = sum(1 for word in query_lower.split() if word in text_lower)
            if score > 0:
                scored_chunks.append((score, {**chunk, "ticker": tkr, "chunk_index": i}))

    # Sort by score descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    # Take top-k
    top_chunks = scored_chunks[:limit]

    retrieval_chunks = [
        RetrievalChunk(
            id=f"demo_{chunk['ticker']}_{chunk['chunk_index']:06d}",
            text=chunk["text"],
            score=score / 10.0,  # Normalize to 0-1 range
            ticker=chunk["ticker"],
            filing_type=chunk["filing_type"],
            filing_date="2024-01-01",
            section=chunk["section"],
            source=f"demo_{chunk['ticker']}_{chunk['filing_type']}_{chunk['chunk_index']}",
            document_id=f"demo_{chunk['ticker']}",
            filename=f"demo_{chunk['ticker']}_{chunk['filing_type']}.pdf",
            page=1,
            chunk_id=f"demo_{chunk['ticker']}_{chunk['chunk_index']:06d}",
        )
        for score, chunk in top_chunks
    ]

    return RetrievalContext(
        query=query,
        chunks=retrieval_chunks,
        retrieval_time_ms=(time.perf_counter() - start) * 1000,
    )