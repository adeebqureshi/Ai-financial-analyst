"""
Run from project root:
    python test_synthesis.py

Tests the exact code path used by the RAG synthesis.
"""
import os
from dotenv import load_dotenv
load_dotenv()

# ── 1. Test raw LLM with a long prompt (like synthesis uses) ─────────────────
print("\n[1] Testing LLM with a long prompt...")
try:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("FREELLMAPI_API_KEY"),
        base_url=os.getenv("FREELLMAPI_BASE_URL"),
        timeout=60,
    )
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        messages=[{"role": "user", "content": "Summarize this in one sentence: Apple reported revenue of $100 billion in Q4 2024, driven by strong iPhone sales and services growth."}],
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
    )
    content = response.choices[0].message.content
    print(f"[1] Response content: {content!r}")
    if not content:
        print("[1] WARNING: content is None/empty — Gemini returned no text!")
    else:
        print("[1] SUCCESS")
except Exception as e:
    import traceback
    print(f"[1] FAILED: {e}")
    traceback.print_exc()

# ── 2. Test through app OpenAIClient ─────────────────────────────────────────
print("\n[2] Testing through app OpenAIClient...")
try:
    import sys; sys.path.insert(0, ".")
    from app.llm.openai_client import OpenAIClient
    from app.llm.models import LLMRequest
    client2 = OpenAIClient()
    result = client2.generate(LLMRequest(
        prompt="Summarize this in one sentence: Apple reported revenue of $100 billion in Q4 2024, driven by strong iPhone sales and services growth."
    ))
    print(f"[2] Response: {result.text!r}")
    if not result.text:
        print("[2] WARNING: empty response text!")
    else:
        print("[2] SUCCESS")
except Exception as e:
    import traceback
    print(f"[2] FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()

# ── 3. Test FinancialAnalystAgent.synthesize directly ────────────────────────
print("\n[3] Testing FinancialAnalystAgent.synthesize...")
try:
    from app.agents.financial_analyst import FinancialAnalystAgent
    from app.agents.intents import AgentIntent
    agent = FinancialAnalystAgent()
    answer, model = agent.synthesize(
        query="What is Apple's revenue?",
        intents=[AgentIntent.FINANCIAL_ANALYSIS],
        evidence={"get_financials": [{"tool": "get_financials", "status": "success", "result": {"revenue": 100_000_000_000}, "error": None}]},
        sources=[],
        tickers=["AAPL"],
    )
    print(f"[3] Model used: {model}")
    print(f"[3] Answer: {answer[:300]}")
    if "could not complete" in answer:
        print("[3] FAILED — still returning LLM_UNAVAILABLE_MESSAGE")
    else:
        print("[3] SUCCESS")
except Exception as e:
    import traceback
    print(f"[3] FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()
