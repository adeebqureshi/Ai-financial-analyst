# Copilot instructions for AI Financial Analyst

## Repository shape

This is a full-stack financial analysis platform:

- `app/` is a Python 3.12 FastAPI backend.
- `frontend/` is a Next.js 16.3 / React 19 application.
- `tests/` contains the backend pytest suite.
- `frontend/**/__tests__/` contains Vitest unit/component tests; `frontend/e2e/` contains Playwright tests.
- `alembic/` contains the PostgreSQL migration history used for the auth and chat databases.
- `docker/docker-compose.yml` starts the production-shaped app, PostgreSQL, and Redis services.

Read the nearest scoped instruction file before changing frontend code. In particular, `frontend/AGENTS.md` is authoritative for the Next.js version in use and requires consulting the matching guides under `frontend/node_modules/next/dist/docs/` before writing Next.js code. `frontend/CLAUDE.md` imports that same guidance.

## Build, test, and lint commands

Run backend commands from the repository root after installing the editable dev dependencies:

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/ -v
python -m pytest tests/ --cov=app --cov-report=term-missing
ruff check app tests
ruff format --check app tests
mypy app
```

Run one backend test or one test file with pytest selectors:

```bash
python -m pytest tests/financial/test_dcf.py -v
python -m pytest tests/financial/test_dcf.py::test_name -v
python -m pytest -k "valuation" -v
```

The pytest configuration sets `pythonpath = ["."]`, discovers tests under `tests/`, and registers an opt-in `integration` marker. Tests use temporary SQLite auth/chat databases and set `AUTH_ENABLED=false` in `tests/conftest.py`; integration tests that require real PostgreSQL or Redis should only be enabled with the documented service URLs.

Run frontend commands from `frontend/`:

```bash
npm install
npm run dev
npm run build
npm run lint
npm run test:run
npm run test:e2e
```

Run a single frontend test:

```bash
npx vitest run components/analysis/__tests__/analysis-view.test.tsx
npx vitest run components/analysis/__tests__/analysis-view.test.tsx -t "test name"
npx playwright test e2e/analysis.spec.ts
npx playwright test e2e/analysis.spec.ts -g "test name"
```

The frontend Vitest config uses `jsdom`, `vitest.setup.ts`, the `@` alias to `frontend/`, and includes `**/*.test.{ts,tsx}`. Playwright starts `npm run dev` automatically at `http://localhost:3000`; the backend must be available at `http://127.0.0.1:8000` for flows that call the API.

For a credential-free local demonstration:

```bash
echo "DEMO_MODE=true" > .env
uvicorn app.main:app --reload
cd frontend
npm run dev
```

The demo path uses deterministic fixtures for AAPL, MSFT, GOOGL, AMZN, and TSLA and does not require external API keys, Qdrant, or live SEC data.

For production-shaped local infrastructure:

```bash
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f app
```

Production PostgreSQL migrations are selected explicitly by database:

```bash
alembic -c alembic.ini -x database=auth upgrade head
alembic -c alembic.ini -x database=chat upgrade head
```

## Architecture and request flow

The backend follows Clean Architecture: dependencies point inward. FastAPI routers and middleware live in `app/api/`; use-case orchestration lives in `app/services/`; domain DTOs/entities and financial calculations live in `app/schemas/`, `app/models/`, `app/financial/`, and related domain packages; external I/O adapters live in ingestion, parsers, retrieval/RAG, LLM, vector-store, database, and infrastructure packages; cross-cutting settings, logging, constants, and exceptions live in `app/core/`.

The normal analysis path is:

1. A frontend page or hook calls a FastAPI endpoint through `frontend/services/api.ts`.
2. API middleware handles CORS, security headers, request IDs, logging, rate limits, auth, and exception translation.
3. A router resolves a service through FastAPI dependencies.
4. The service coordinates market/SEC/document data, financial calculations, retrieval, and the agent pipeline.
5. `CoordinatorAgent` plans work, executes only selected tools, gathers evidence, invokes the financial analyst, and passes the result through the auditor/report writer as appropriate.
6. The response is returned in the shared `APIResponse[T]` envelope and rendered by the frontend.

Chat streaming uses `POST /chat/stream` and Server-Sent Events. Tool execution is blocking/threaded; only the synthesis phase streams tokens. Keep the event names and payload shape in sync with `frontend/services/api.ts` (`plan`, `token`, `done`, and `error`).

The frontend uses the Next.js App Router. Route pages under `frontend/app/(app)/` compose feature components; client-side data fetching and caching are handled by TanStack React Query providers/hooks; API serialization, errors, SSE parsing, and the backend base URL are centralized in `frontend/services/api.ts`. The Next rewrite maps `/api/backend/*` to the local FastAPI server. Keep domain types in `frontend/types/analysis.ts` aligned with backend response schemas.

Infrastructure is intentionally degradable in development: SQLite replaces PostgreSQL, in-process behavior can replace Redis, and Chroma/local memory can replace Qdrant. Production uses PostgreSQL, Redis, and Qdrant-compatible vector storage as configured by environment settings.

## Codebase-specific conventions

- Load configuration through `app.core.config.get_settings()` / `Settings`; settings are validated, frozen, and cached. Do not read secrets directly from `os.environ` in application code or bypass `SecretStr`.
- Use the existing dependency-injection/container patterns when wiring services, providers, databases, caches, or vector stores. Prefer interfaces/provider factories over hard-coding a vendor.
- Preserve demo mode as a complete provider substitution path. Do not scatter demo-only conditionals or present synthetic values as live financial data; demo output must remain visibly labeled.
- API routes validate and normalize inputs (especially ticker symbols), call services, and return the established `APIResponse` envelope. Put business orchestration in services rather than routers.
- Financial analysis is evidence-first: retrieval/tool results are the source context for LLM synthesis, and auditor checks protect against ticker leakage, unsupported claims, and fabrication.
- Use domain exception subclasses from `app/core/exceptions.py`; let the existing API exception handlers translate them rather than returning ad-hoc error payloads.
- Obtain module loggers with `get_logger(__name__)` and use lazy `%` formatting. Follow `docs/OBSERVABILITY.md`: never log secrets, tokens, prompts, completions, full financial payloads, document contents, or database URLs. Include safe IDs, operation names, and timings where useful.
- Preserve ownership scoping for authenticated chat sessions and uploaded documents. Anonymous access is intentionally subject to reduced rate limits.
- For frontend data access, use the shared `api` client and React Query hooks instead of calling `fetch` from individual components. Preserve `ApiError` retry/auth semantics and existing query-key patterns.
- Keep server/client boundaries explicit in the App Router. Components using hooks, browser APIs, or streaming must remain client components; route pages can fetch server-side where the existing pattern does so.
- Use the `@/` import alias in frontend TypeScript. Match the existing component organization and Tailwind styling conventions rather than introducing a parallel UI abstraction.
- When changing frontend Next.js behavior, read the version-matched Next.js documentation required by `frontend/AGENTS.md`; `next dev` may regenerate that file’s managed block.
- When changing auth or chat schema models for PostgreSQL, update the correct Alembic history (`auth` or `chat`) and consider the SQLite development fallback and migration tests.
- Keep endpoint, schema, service, frontend type, and test changes synchronized. A backend response shape change normally requires updates to `app/schemas`, `frontend/types`, `frontend/services/api.ts`, affected hooks/components, and focused tests.

