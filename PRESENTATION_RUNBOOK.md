# Presentation Runbook — AI Financial Analyst / EquityIQ

Prepared: 2026-10-09. All items below were actually verified; see §8 for status.

## 1. Start everything (Windows PowerShell, project root)

```powershell
# 1) Qdrant (expected local install; must listen on 6333 + 6334)
C:\Users\ASUS\qdrant-server\qdrant.exe
# verify:  Invoke-WebRequest http://127.0.0.1:6333/healthz  -> 200 "healthz check passed"

# 2) Backend (project root)
python -m uvicorn app.main:app --port 8000
# wait ~60-90s for embedding model + reranker pre-warm, then:
Invoke-WebRequest http://127.0.0.1:8000/readiness
# expect: {"status":"ready","ready":true,"database":true,"vector_store":true,...}

# 3) Frontend (separate terminal)
cd frontend; npm run dev
# open http://localhost:3000
```

Startup order matters: **Qdrant → backend → frontend**. The backend's startup
log must show `Infrastructure check passed: vector_store` (not FAILED).

## 2. Pre-presentation checks (2 minutes)

| Check | Command / URL | Expected |
|---|---|---|
| Qdrant HTTP | `http://127.0.0.1:6333/healthz` | 200 `healthz check passed` |
| Qdrant gRPC | `Get-NetTCPConnection -State Listen \| ? {$_.LocalPort -eq 6334}` | one listener |
| Collection | `http://127.0.0.1:6333/collections/financial_documents` | exists, `points_count: 121` |
| Backend health | `http://127.0.0.1:8000/health` | 200 |
| Backend readiness | `http://127.0.0.1:8000/readiness` | `"vector_store":true` |
| Frontend | `http://localhost:3000/research` | Research page loads, `apple 10k.pdf` listed, Indexed |

## 3. Environment variables (names only — never show values on screen)

Required: `FREELLMAPI_API_KEY` (OpenRouter), `QDRANT_URL=http://localhost:6333`,
`QDRANT_COLLECTION=financial_documents`, `LLM_MODEL=apodex/apodex-1.1-mini:free`,
`FREELLMAPI_BASE_URL=https://openrouter.ai/api/v1`,
`EMBEDDING_MODEL=all-MiniLM-L6-v2`, `EMBEDDING_DIMENSION=384`.
Optional market data: `FMP_API_KEY`. All are already set in `.env`.

## 4. Demo sequence (recommended, all pre-tested)

1. **Research page** → select `apple 10k.pdf` (121 chunks, Indexed).
2. **"Summarize key risks"** → grounded answer, ~2.6k chars, 5 citations
   (pp. 30, 12, 15, 14, 51). Verified live 2026-10-09.
3. **"Compare margins by segment"** → segment tables, pp. 19–50. Verified live.
4. **Company analysis** → ticker `AAPL` (needs `FMP_API_KEY`; falls back gracefully).
5. **Compare** → `AAPL` vs `MSFT`.
6. **Report download** from a completed analysis.

## 5. If an AI answer comes back empty or fails

OpenRouter intermittently returns zero-token streams (~1 in 3). The backend logs
`LLM stream completed with zero content tokens` and surfaces an error event —
it never fabricates an answer. Recovery: **click retry / resend the same message**
(verified: retry succeeds; no duplicate user message, history intact).

## 6. If something stops

- Backend down → restart command in §1; wait for pre-warm; re-check `/readiness`.
- Qdrant down → restart `qdrant.exe`; backend recovers without restart
  (next `/readiness` poll shows `vector_store:true`).
- Frontend down → `cd frontend; npm run dev`.
- Never delete/recreate the Qdrant collection or re-upload the 10-K.

## 7. Honest offline fallback (LLM provider down)

Say: "The external model is unreachable; retrieval still works — here are the
exact 10-K chunks the system found." Show the cited chunks/pages from the
Research panel. Do not present anything as model output that is not.

## 8. Verification status

Verified live: backend health/readiness, Qdrant + 121-point collection,
Research chat "Summarize key risks" + "Compare margins by segment" with
citations, all frontend routes (9/9 HTTP 200), production build, planner
routing for all 7 RAG questions, relevance-floor + insufficient-evidence paths.
Verified by tests only: company analysis/compare (need live FMP), report PDF
download, streaming cancellation, responsive layouts, hosted deployment.
