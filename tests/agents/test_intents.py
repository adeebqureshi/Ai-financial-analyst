from app.agents.intents import AgentIntent, IntentClassifier


def _classify(query: str, document_id: str | None = None):
    return [intent.value for intent in IntentClassifier().classify(query, document_id)]


def test_price_question_is_market_data():
    assert _classify("What is Apple's current price?") == ["MARKET_DATA"]


def test_document_question_is_document_only():
    assert _classify(
        "What does Apple's annual report say about supply chain risk?"
    ) == ["DOCUMENT_RESEARCH"]


def test_document_id_forces_document_intent():
    assert _classify("What is the revenue trend?", document_id="doc1") == [
        "DOCUMENT_RESEARCH"
    ]


def test_valuation_intent():
    assert AgentIntent.VALUATION.value in _classify("Is Apple undervalued?")


def test_comparison_intent():
    intents = _classify("Compare Apple and Microsoft.")

    assert AgentIntent.COMPARISON.value in intents

    assert "DOCUMENT_RESEARCH" not in intents


def test_mixed_document_and_comparison():
    intents = _classify(
        "Compare Apple and Microsoft using their annual reports "
        "and tell me which is a better investment."
    )

    assert AgentIntent.COMPARISON.value in intents

    assert AgentIntent.DOCUMENT_RESEARCH.value in intents


def test_mixed_valuation_health_risk_document():
    intents = _classify(
        "Analyze Nvidia's valuation, financial health, and risks "
        "mentioned in its annual report."
    )

    assert AgentIntent.DOCUMENT_RESEARCH.value in intents
    assert AgentIntent.VALUATION.value in intents
    assert AgentIntent.FINANCIAL_ANALYSIS.value in intents
    assert AgentIntent.RISK_ANALYSIS.value in intents


def test_report_generation_action():
    assert AgentIntent.REPORT_GENERATION.value in _classify(
        "Build an investment thesis for Microsoft."
    )


def test_bare_report_word_is_not_report_intent():
    # "annual report" describes a document, it is not a request to generate one.
    intents = _classify(
        "What does Apple's annual report say about supply chain risk?"
    )

    assert AgentIntent.REPORT_GENERATION.value not in intents
