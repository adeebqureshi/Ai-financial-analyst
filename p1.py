import os
os.environ["LLM_PROVIDER"] = "mock"
import io, asyncio, json
import fitz
from app.main import app

def make_pdf(text):
    d = fitz.open(); p = d.new_page(); p.insert_text((72, 72), text)
    b = io.BytesIO(); d.save(b); d.close(); return b.getvalue()

async def run():
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        out = []
        txt = (
            "Apple faces significant risk factors. The company depends on a "
            "concentrated supply chain and global macroeconomic conditions. "
            "Management highlighted competitive risk in smartphones and services. "
            "Currency fluctuations and component cost increases are key risks."
        )
        r = await ac.post("/documents/upload", files={"file": ("AAPL 10-K.pdf", make_pdf(txt), "application/pdf")})
        out.append("UPLOAD %s %s" % (r.status_code, r.json().get("success")))
        data = r.json().get("data", {})
        out.append("DOC %s chunks=%s pages=%s status=%s" % (data.get("document_id"), data.get("chunks"), data.get("pages"), data.get("status")))
        did = data["document_id"]
        s = await ac.post("/search", json={"query": "What are Apple's major risk factors?", "limit": 3, "document_id": did})
        sout = s.json()
        out.append("SEARCH %s total=%s" % (s.status_code, sout.get("data", {}).get("total")))
        hits = sout.get("data", {}).get("hits", [])
        for h in hits[:3]:
            out.append("HIT doc=%s page=%s text=%r" % (h.get("document_id"), h.get("page"), h.get("text", "")[:80]))
        c = await ac.post("/chat", json={"message": "What are Apple's major risk factors?", "document_id": did})
        cout = c.json()
        out.append("CHAT %s" % c.status_code)
        out.append("CHAT_MSG %r" % cout.get("data", {}).get("message", "")[:200])
        out.append("CHAT_SOURCES %s" % json.dumps(cout.get("data", {}).get("sources", [])))
        await ac.delete("/documents/%s" % did)
        with open("p1_out.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(out))

if __name__ == "__main__":
    asyncio.run(run())