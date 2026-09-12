# AI Financial Analyst — Architecture Documentation

This document describes the architecture of the AI Financial Analyst platform as implemented. It reflects the actual codebase — not aspirational design.

---

## 1. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  Next.js/React  │    │  REST Clients   │    │  WebSocket (chat)       │ │
│  │  Frontend       │    │  (curl, etc.)   │    │  Streaming              │ │
│  └────────┬────────┘    └────────┬────────┘    └───────────┬─────────────┘ │
└───────────│──────────────────────│──────────────────────────│──────────────┘
            ▼                      ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API GATEWAY (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  CORS • Security Headers • Rate Limiting • Request Logging           │  │
│  │  JWT Auth (opt-in) • Exception Handlers • OpenAPI Docs               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  Routers: /analyze  /chat  /report  /search  /company  /valuation         │
│           /risk  /ratios  /health  /screen  /compare  /documents  /version │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SERVICE LAYER (Use Cases)                           │
│  ┌──────────────┐ ┌──────────┐ ┌────────────┐ ┌─────────┐ ┌──────────────┐ │
│  │ AnalysisSvc  │ │ ChatSvc  │ DocumentSvc  │ ReportSvc│ CompanySvc     │ │
│  │ ValuationSvc │ │ ScreenSvc│ CompareSvc   │ FilingSvc│ MarketSvc      │ │
│  └──────────────┘ └──────────┘ └────────────┘ └─────────┘ └──────────────┘ │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AGENTIC ORCHESTRATION LAYER                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ CoordinatorAgent (orchestrator)                                      │  │
│  │   ├── PlannerAgent        → intent detection, tool selection         │  │
│  │   ├── ToolRegistry        → executes 11 financial tools              │  │
│  │   ├── FinancialAnalystAgent → evidence-grounded synthesis            │  │
│  │   ├── AuditorAgent        → grounding / ticker isolation / no-fab    │  │
│  │   └── ReportWriterAgent   → structured markdown reports              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬─────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA & INFRASTRUCTURE LAYER                           │
│  ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────────┐ │
│  │ PostgreSQL   │ │ Redis      │ │ Qdrant     │ │ Sandbox (subprocess)   │ │
│  │ (auth, chat) │ │ (cache,    │ │ (vector    │ │ (code execution)       │ │
│  │              │ │  rate lim) │ │  store)    │ │                        │ │
│  └──────────────┘ └────────────┘ └────────────┘ └────────────────────────┘ │
│  ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────────┐ │
│  │ yfinance     │ │ FMP/SEC    │ │ Sentence-  │ │ ChromaDB (dev)         │ │
│  │ (market)     │ │ EDGAR      │ │ Transformers│ │ (local vector store)   │ │
│  └──────────────┘ └────────────┘ └────────────┘ └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend → FastAPI → Services/Agents → Database/Providers Flow

### Request Flow (e.g., `POST /analyze`)

1. **Frontend** sends request with ticker + query → FastAPI router
2. **Middleware** applies: CORS, security headers, rate limiting, request ID correlation
3. **Auth dependency** (optional) validates JWT → extracts `user_id`
4. **Router** calls `AnalysisService.generate_analysis(ticker, query, user_id)`
5. **Service** instantiates/uses `CoordinatorAgent` (or direct pipeline)
6. **Coordinator** runs the agentic pipeline:
   - `PlannerAgent.classify()` → detects intents, resolves pronouns, selects tools
   - `ToolRegistry.execute()` → runs selected tools (market data, financials, valuation, RAG, etc.)
   - `FinancialAnalystAgent.synthesize()` → evidence-grounded LLM answer
   - `AuditorAgent.audit_evidence()` → verifies grounding, ticker isolation, no fabrication
   - (Optional) `ReportWriterAgent.write()` → structured markdown report
7. **Service** wraps result in `APIResponse[AnalysisData]` → returns JSON

### Streaming Flow (`/chat/stream`)

Same pipeline but `FinancialAnalystAgent.stream_synthesize()` yields tokens → SSE stream.

### Tool Execution (11 Tools)

| Tool | Purpose |
|------|---------|
| `get_company` | Company profile from SEC/EDGAR |
| `get_market_data` | Live quotes, beta, market cap |
| `get_financials` | Income statement, balance sheet, cash flow |
| `calculate_valuation` | DCF intrinsic value, recommendation |
| `calculate_financial_health` | Composite score + Piotroski/Altman/Beneish |
| `calculate_risk` | Risk level + score breakdown |
| `search_documents` | Hybrid RAG (semantic + BM25 + rerank) |
| `run_calculation` | Sandboxed Python execution |
| `get_news` | Financial news (optional) |
| `compare_companies` | Multi-ticker comparison |
| `screen_stocks` | Filter by health/valuation criteria |

---

## 3. Technology Choices & Rationale

### OpenAI (LLM Provider)
- **Chosen for**: Function calling support, structured output, streaming, ecosystem maturity
- **Used via**: `OpenAIClient` abstraction with provider factory — swappable
- **Fallback**: `llm_provider="mock"` for tests/demo (no API key needed)
- **Token quota**: Per-user daily limit enforced at chat endpoint

### Qdrant (Vector Store)
- **Chosen for**: Production-grade vector similarity search, payload filtering, horizontal scaling
- **Interface**: `VectorStore` abstract base → `QdrantStore` implementation
- **Dev fallback**: `ChromaDB` (in-memory/local) when Qdrant unavailable
- **Embeddings**: `text-embedding-3-small` (1536 dim) via OpenAI

### PostgreSQL (Primary Database)
- **Auth DB**: `users` table (Alembic migrations)
- **Chat DB**: `chat_sessions`, `chat_messages` tables (Alembic migrations)
- **ORM**: SQLAlchemy 2.0 async
- **Dev fallback**: SQLite (`sqlite:///./data/auth.db`, `chat.db`) — zero-config local dev

### Redis (Caching & Rate Limiting)
- **Quote cache**: TTL + stale-while-revalidate for market data
- **Rate limiting**: Distributed token bucket (falls back to in-process when Redis down)
- **Chat context cache**: Recent session context for fast history loading
- **Optional**: App degrades gracefully if Redis unavailable

### Hybrid RAG (Semantic + BM25 + Cross-Encoder Rerank)
- **Semantic**: `sentence-transformers/all-MiniLM-L6-v2` (384 dim) for dense retrieval
- **Keyword**: BM25 (rank-bm25) for exact term matching
- **Fusion**: Reciprocal rank fusion (RRF) via score aggregation
- **Rerank**: Cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) for precision
- **Why hybrid**: Pure semantic misses exact tickers/terms; pure keyword misses semantic intent

---

## 4. Agent Pipeline: Planner → Coordinator → Specialist → Auditor

### Why This Pattern?

| Agent | Responsibility | Why Separate |
|-------|----------------|--------------|
| **Planner** | Intent classification + minimal tool selection + pronoun resolution | Pure CPU/logic — deterministic, testable, no I/O |
| **Coordinator** | Orchestration: plan → execute tools → collect evidence → synthesize → audit | Single flow controller; injectable deps for testing |
| **FinancialAnalyst** | Evidence-grounded LLM synthesis | Domain expertise; streaming support |
| **Auditor** | Post-hoc verification: grounding, ticker isolation, no fabrication | Independent quality gate; catches LLM hallucinations |
| **ReportWriter** | Structured markdown report from evidence blocks | Separation of synthesis vs. formatting |

### Key Design Decisions

- **No speculative tool execution** — Planner selects exact tools; Coordinator runs only those
- **Evidence-first** — LLM never sees raw query alone; always gets tool results + sources
- **Auditor as safety net** — Runs after synthesis; appends warning note if issues found
- **Conversation memory** — `ConversationMemory` stores last N turns for pronoun resolution
- **Streaming only at synthesis** — Tool execution is blocking (threaded); only LLM streams

---

## 5. Security & Authentication Architecture

### Authentication (JWT + PBKDF2)
- **Password hashing**: PBKDF2-HMAC-SHA256, 240k iterations, 16-byte salt
- **Constant-time verification**: `hmac.compare_digest`
- **Access tokens**: HS256 JWT, 60-min default expiry, `sub` = user_id, `jti` for revocation
- **Ephemeral dev secret**: Process-random fallback; production MUST set `AUTH_SECRET_KEY`

### Authorization
- **Secure by default**: `AUTH_ENABLED=true` requires JWT on business endpoints
- **Ownership isolation**: Chat sessions scoped to `owner_id` (user_id)
- **Document ownership**: Uploaded documents tagged with `owner_id`
- **Anonymous access**: Allowed with reduced rate limits (10% of authenticated)

### Rate Limiting
- **Algorithm**: Token bucket (Redis-backed, in-memory fallback)
- **Tiers**: Per-endpoint limits (chat: 20/min, analyze: 10/min, sandbox: 5/min)
- **Anonymous multiplier**: 0.1x authenticated limits
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

### Security Headers
- `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`
- `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security` (prod)

### CORS
- **Dev/Test**: Wildcard origins, no credentials
- **Staging**: Localhost origins if `CORS_ORIGINS` unset
- **Production**: Explicit `CORS_ORIGINS` required; fails fast if missing

---

## 6. Demo Mode & Evaluation Setup

### Demo Mode (`DEMO_MODE=true`)
- **Purpose**: Fully self-contained evaluation without external credentials
- **Fixtures**: 5 companies (AAPL, MSFT, GOOGL, AMZN, TSLA) with deterministic synthetic data
- **Providers swapped**:
  - `DemoMarketProvider` → implements `MarketDataProvider` interface
  - `DemoFinancialDataService` → replaces `FinancialDataService`
  - `DemoSECService` → replaces `SECService`
  - `MemoryVectorStore` → replaces `QdrantStore` (pre-populated with demo embeddings)
- **No scattered conditionals** — Services auto-select via `Settings.is_demo_mode`
- **All demo data labeled**: `[DEMO / SYNTHETIC DATA]` in UI, API, and `/version` endpoint

### Evaluation (`app/evaluation/run.py`)
- **Type**: Synthetic reference evaluation (not live backtesting)
- **Metrics**: Piotroski F-Score, Altman Z-Score, Beneish M-Score, DCF intrinsic value
- **Data source**: Demo fixtures (same 5 companies)
- **Output**: Per-ticker per-metric comparison (calculated vs. reference), relative error %, pass/fail at configurable tolerance
- **Purpose**: Validates engine wiring and numerical stability — NOT predictive accuracy

---

## 7. Key Alternatives & Trade-offs

| Decision | Chosen | Alternative Considered | Trade-off |
|----------|--------|------------------------|-----------|
| **Architecture** | Clean Architecture (monolith) | Microservices | Simplicity, deployment, debugging vs. independent scaling |
| **LLM** | OpenAI | Anthropic, local (Ollama) | Function calling maturity, streaming, cost |
| **Vector Store** | Qdrant | Pinecone, Weaviate, Milvus | Self-hostable, filtering, performance |
| **Embeddings** | OpenAI `text-embedding-3-small` | Sentence-Transformers local | Quality vs. offline capability |
| **RAG** | Hybrid (dense + BM25 + rerank) | Pure semantic / pure keyword | Recall + precision vs. complexity |
| **Auth** | JWT + PBKDF2 | OAuth2/OIDC, bcrypt/argon2 | Zero native deps, portable, standard |
| **Market Data** | yfinance (unofficial) + FMP fallback | Bloomberg, Refinitiv, Polygon | Cost-free dev vs. no SLA, unofficial |
| **Sandbox** | Subprocess + resource limits | WASM, gVisor, Firecracker | Simplicity vs. isolation strength |
| **Async** | Threaded blocking I/O (`asyncio.to_thread`) | Fully async drivers | Compatibility with sync libs (yfinance, sqlalchemy sync) |
| **Config** | Pydantic Settings (frozen) | python-dotenv, raw os.environ | Validation, immutability, type safety |

---

## 8. Why We Intentionally Avoided "Enterprise" Infrastructure

This is a **final-year college project** demonstrating software engineering principles — not a production SaaS platform.

| Avoided | Reason |
|---------|--------|
| **Kubernetes** | Adds operational complexity (cluster, Helm, CNI, ingress, cert-manager) without architectural benefit for a single-instance app. FastAPI + gunicorn + systemd/docker-compose is sufficient. |
| **Kafka/Message Queues** | No event-driven microservices; request/response + background jobs (chat retention) handled by simple APScheduler/cron. |
| **Service Mesh (Istio/Linkerd)** | No inter-service communication; single process. |
| **Distributed Tracing (Jaeger/Zipkin)** | Correlation IDs + structured logging cover observability needs. |
| **Feature Flags (LaunchDarkly/Unleash)** | Config-driven provider selection (`market_primary_provider`, `llm_provider`) covers toggling. |
| **Secrets Manager (Vault/AWS Secrets)** | `.env` + `SecretStr` + `AUTH_SECRET_KEY` rotation documented; sufficient for scope. |
| **CI/CD Pipeline (GitHub Actions/GitLab CI)** | Documented in README; project focuses on code architecture, not pipeline yaml. |
| **Multi-region / HA** | Single-region deployment target; SQLite/PostgreSQL + Redis cover state. |
| **GraphQL** | REST + OpenAPI meets all frontend needs; no over-fetching/under-fetching problem. |
| **gRPC** | No internal service boundaries; HTTP/JSON is universal. |

### What This Project *Does* Demonstrate

- **Clean Architecture** with dependency inversion (interfaces in core, implementations in infrastructure)
- **SOLID principles** applied consistently (see README for mapping)
- **Agentic orchestration** with evidence grounding and auditor safety net
- **Hybrid RAG** with semantic + keyword + rerank fusion
- **Security-first defaults** (auth on, rate limits, secure headers, constant-time crypto)
- **Graceful degradation** (SQLite fallback, in-memory cache, mock LLM, demo mode)
- **Comprehensive testing** (unit, integration, contract, property-based where applicable)
- **Type safety** (mypy strict, pydantic validation, frozen config)

---

## Appendix: Key Module Map

```
app/
├── api/              # FastAPI routers, middleware, deps, exceptions
├── agents/           # Planner, Coordinator, Analyst, Auditor, ReportWriter, Tools
├── auth/             # JWT, PBKDF2, user service, DB
├── chat/             # Chat persistence (SQL + Redis cache)
├── core/             # Config, logging, exceptions, constants (innermost layer)
├── data/             # yfinance wrapper, financial statements
├── db/               # (empty — DB init in auth/chat modules)
├── demo/             # Synthetic fixtures & providers for DEMO_MODE
├── embeddings/       # Embedding model abstraction
├── enums/            # StrEnum types (Environment, FilingType, etc.)
├── evaluation/       # Synthetic reference evaluation entry point
├── financial/        # DCF, WACC, Piotroski, Altman, Beneish, ratios, growth
├── ingestion/        # SEC EDGAR, FMP, PDF/XBRL/HTML parsers, document pipeline
├── infrastructure/   # Container (health checks), provider factories
├── llm/              # OpenAIClient, provider factory, mock provider
├── models/           # SQLAlchemy ORM models (User, ChatSession, etc.)
├── orchestrator/     # Legacy pipeline (FinancialPipeline) — retained for compat
├── parsers/          # XBRL, HTML, table extraction
├── portfolio/        # CAGR, Beta (simple financial math)
├── rag/              # Hybrid retriever, BM25, cross-encoder, vector stores
├── recommendation/   # Buy/Hold/Sell logic from valuation + health
├── retrieval/        # Domain models for retrieval (RetrievedChunk, RetrievalContext)
├── reports/          # Report models (InvestmentReport, markdown)
├── sandbox/          # Subprocess code executor with resource limits
├── schemas/          # Pydantic request/response DTOs
├── services/         # Use-case services (Analysis, Chat, Document, etc.)
├── utils/            # Ticker normalization, helpers
├── vectorstore/      # VectorStore abstraction + Qdrant/Chroma impl
├── workflow/         # (legacy) workflow orchestration
└── main.py           # App factory, lifespan, middleware, router registration
```

---

*Generated from codebase inspection — reflects actual implementation as of current commit.*