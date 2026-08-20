import os
os.environ["LLM_PROVIDER"] = "mock"
import asyncio, json
from app.main import app

async def run():
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        out = []
        # P3 report
        r = await ac.post("/report", json={"ticker": "AAPL", "query": ""})
        out.append("REPORT %s success=%s" % (r.status_code, r.json().get("success")))
        rd = r.json().get("data", {})
        out.append("REPORT ticker=%s format=%s content_len=%s" % (rd.get("ticker"), rd.get("format"), len(rd.get("content", "") or "")))
        # P4 compare
        rc = await ac.post("/compare", json={"tickers": ["AAPL", "MSFT"]})
        out.append("COMPARE %s success=%s best=%s" % (rc.status_code, rc.json().get("success"), rc.json().get("data", {}).get("best")))
        for item in rc.json().get("data", {}).get("results", []):
            out.append("  %s name=%s iv=%.2f upside=%.2f rec=%s health=%s" % (item.get("ticker"), item.get("name"), item.get("intrinsic_value",0), item.get("upside",0), item.get("recommendation"), item.get("health_score")))
        # P5 screen (single candidate)
        sc = await c.post("/screen", json={
            "statement": {"revenue": 416161, "operating_income": 130731, "net_income": 112010, "total_assets": 359241, "total_liabilities": 285508, "cash": 35934, "debt": 98657, "shares_outstanding": 15438, "free_cash_flow": 98767},
            "valuation": {"current_price": 313.19, "growth_rate": 0.08, "risk_free_rate": 0.0425, "beta": 1.2, "market_return": 0.10, "tax_rate": 0.21},
            "min_piotroski": 7, "min_altman": 3, "max_beneish": -1.8, "min_upside": 0,
        })
        out.append("SCREEN %s success=%s total=%s" % (sc.status_code, sc.json().get("success"), sc.json().get("data", {}).get("total")))
        with open("p_out.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(out))

if __name__ == "__main__":
    asyncio.run(run())