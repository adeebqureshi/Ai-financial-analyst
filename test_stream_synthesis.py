"""Minimal end-to-end LLM diagnostics for the AI Insights synthesis path.

Uses the EXISTING client/configuration (no separate config), so it exercises
exactly what the chat/copilot pipeline uses:

  A. minimal non-streaming completion   (OpenAIClient.generate)
  B. minimal streaming completion       (AsyncOpenAIClient.stream)
  C. sync tool-result synthesis         (FinancialAnalystAgent.synthesize)
  D. streaming tool-result synthesis    (FinancialAnalystAgent.stream_synthesize)

Run:  .venv\\Scripts\\python.exe test_stream_synthesis.py
Pytest ignores this file (testpaths = ["tests"]).
"""

import asyncio
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

sys.path.insert(0, ".")

from app.core.config import get_settings

s = get_settings()
key = s.freellmapi_api_key_str or s.openai_api_key_str
from urllib.parse import urlparse
host = urlparse(s.freellmapi_base_url).netloc or "default"
print("\n[config] (safe — no secrets)")
print(f"  provider    = {s.llm_provider!r}")
print(f"  model       = {s.llm_model!r}")
print(f"  base host   = {host!r}")
print(f"  key present = {bool(key.strip())}")
print(f"  timeout     = {s.api_timeout}s  max_tokens={s.llm_max_tokens}  temp={s.llm_temperature}")

failures: list[str] = []

# ---- A. minimal non-streaming completion -----------------------------------
print("\n[A] minimal completion (sync client) ...")
try:
    from app.llm.openai_client import OpenAIClient
    from app.llm.models import LLMRequest
    r = OpenAIClient().generate(
        LLMRequest(prompt="Explain in one sentence what revenue means.")
    )
    if not r.text or "could not complete" in r.text:
        failures.append("A: empty/unavailable sync completion")
        print(f"  FAILED — {r.text!r}")
    else:
        print(f"  OK — {r.text[:160]!r}")
except Exception as exc:
    failures.append(f"A: {type(exc).__name__}: {exc}")
    print(f"  FAILED — {type(exc).__name__}: {exc}")

# ---- B. minimal streaming completion ---------------------------------------
print("\n[B] minimal completion (async stream client) ...")
async def _stream_once() -> str:
    from app.llm.async_openai_client import AsyncOpenAIClient
    from app.llm.models import LLMRequest
    chunks: list[str] = []
    async for tok in AsyncOpenAIClient().stream(
        LLMRequest(prompt="Explain in one sentence what net income means.")
    ):
        chunks.append(tok)
    return "".join(chunks)
try:
    text = asyncio.run(_stream_once())
    if not text:
        failures.append("B: empty streamed completion")
        print("  FAILED — no tokens streamed")
    else:
        print(f"  OK — {len(text)} chars, {text[:120]!r}")
except Exception as exc:
    failures.append(f"B: {type(exc).__name__}: {exc}")
    print(f"  FAILED — {type(exc).__name__}: {exc}")

# ---- mock structured tool result (Step 6) ----------------------------------
MOCK_EVIDENCE = {
    "get_financials": [
        {
            "tool": "get_financials",
            "status": "done",
            "detail": "financial statements",
            "result": {
                "company": "GOOGL",
                "revenue": "350,025 (FY2024, USD millions)",
                "net_income": "100,118 (FY2024, USD millions)",
                "source": "financial_analysis",
            },
            "error": None,
        }
    ]
}
QUERY = "What was Google's revenue and net income in the latest fiscal year?"

# ---- C. sync tool-result synthesis -----------------------------------------
print("\n[C] sync tool-result synthesis (FinancialAnalystAgent.synthesize) ...")
try:
    from app.agents.financial_analyst import FinancialAnalystAgent
    from app.agents.intents import AgentIntent
    agent = FinancialAnalystAgent()
    answer, model = agent.synthesize(
        query=QUERY,
        intents=[AgentIntent.FINANCIAL_ANALYSIS],
        evidence=MOCK_EVIDENCE,
        sources=[],
        tickers=["GOOGL"],
    )
    if "could not complete" in answer:
        failures.append("C: sync synthesis returned LLM_UNAVAILABLE_MESSAGE")
        print("  FAILED — LLM_UNAVAILABLE_MESSAGE returned")
    elif "100,118" not in answer and "100.1" not in answer:
        failures.append(f"C: answer does not carry the evidence figures — {answer[:200]}")
        print(f"  SUSPECT — {answer[:300]!r}")
    else:
        print(f"  OK — {answer[:300]!r}")
except Exception as exc:
    failures.append(f"C: {type(exc).__name__}: {exc}")
    print(f"  FAILED — {type(exc).__name__}: {exc}")

# ---- D. streaming tool-result synthesis ------------------------------------
print("\n[D] streaming tool-result synthesis (stream_synthesize) ...")
async def _stream_synth() -> str:
    from app.agents.financial_analyst import FinancialAnalystAgent
    from app.agents.intents import AgentIntent
    agent = FinancialAnalystAgent()
    parts: list[str] = []
    async for tok in agent.stream_synthesize(
        query=QUERY,
        intents=[AgentIntent.FINANCIAL_ANALYSIS],
        evidence=MOCK_EVIDENCE,
        sources=[],
        tickers=["GOOGL"],
    ):
        parts.append(tok)
    return "".join(parts)
try:
    streamed = asyncio.run(_stream_synth())
    if not streamed or "could not complete" in streamed:
        failures.append("D: streaming synthesis unavailable/empty")
        print("  FAILED — LLM_UNAVAILABLE_MESSAGE/empty returned")
    elif "100,118" not in streamed and "100.1" not in streamed:
        failures.append(f"D: streamed answer missing evidence figures — {streamed[:200]}")
        print(f"  SUSPECT — {streamed[:300]!r}")
    else:
        print(f"  OK — {len(streamed)} chars, {streamed[:300]!r}")
except Exception as exc:
    failures.append(f"D: {type(exc).__name__}: {exc}")
    print(f"  FAILED — {type(exc).__name__}: {exc}")

print()
if failures:
    print("FAILURES:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL LLM DIAGNOSTICS PASSED")
