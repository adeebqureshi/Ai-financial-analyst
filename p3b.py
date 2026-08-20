import os
os.environ["LLM_PROVIDER"] = "mock"
import asyncio, json
from app.main import app

async def run():
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        out = []
        r = await ac.post("/report", json={"ticker": "AAPL", "query": "Write a financial analysis report on AAPL based on its fundamentals, valuation and financial health."})
        rd = r.json().get("data", {}) if r.status_code == 200 else {}
        out.append("REPORT status=%s success=%s format=%s len=%s head=%r" % (
            r.status_code, r.json().get("success"),
            rd.get("format"), len(rd.get("content", "") or ""),
            (rd.get("content") or "")[:120]))
        rc = await ac.post("/compare", json={"tickers": ["AAPL", "MSFT"]})
        out.append("COMPARE status=%s success=%s best=%s" % (rc.status_code, rc.json().get("success"), rc.json().get("data", {}).get("best")))
        for it in rc.json().get("data", {}).get("results", []):
            out.append("  %s %s iv=%.2f upside=%.2f rec=%s health=%s" % (it.get("ticker"), it.get("name"), it.get("intrinsic_value",0), it.get("upside",0), it.get("recommendation"), it.get("health_score")))
        with open("p_out.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(out))

if __name__ == "__main__":
    asyncio.run(run())