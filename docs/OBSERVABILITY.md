# Observability Guide

How logging works in this application, what is logged, what is intentionally
never logged, how to configure it, and how the request ID flows through the
stack. This is deliberately a lightweight, standard-library-based setup — no
external monitoring stack is required.

---

## 1. Architecture

| Component | Location | Purpose |
|---|---|---|
| Logger factory | `app/core/logging.py` (`get_logger`) | Every module obtains a logger via `logger = get_logger(__name__)`; logging is configured lazily on first use. |
| Setup | `app/core/logging.py` (`setup_logging`) | Idempotent root-logger configuration: Rich console handler + rotating file handler. |
| Formats | `app/core/constants.py` | `LOG_FILE_FORMAT` (includes `request_id`), `LOG_CONSOLE_FORMAT`. |
| Request-ID context | `app/infrastructure/request_id.py` | A `ContextVar` holding the current correlation ID; `get_request_id()`, `set_request_id()`, `bind_request_id()`. |
| Request-ID filter | `app/core/logging.py` (`RequestIDFilter`) | Injects `request_id` into every log record (from the ContextVar). |
| HTTP middleware | `app/api/middleware/request_logging.py` (`RequestLoggingMiddleware`) | Generates/propagates the request ID, stamps `X-Request-ID` on responses, logs method/path/status/duration per request. |

Log output:

- **Console** — colored, human-friendly (Rich). `LOG_LEVEL` controls verbosity.
- **File** — `storage/logs/app.log`, machine-parseable, rotated at 10 MB with
  5 backups. Each line looks like:

  ```
  2026-09-07 12:00:00 | INFO | app.services.document_service | upload:410 | request_id=9c1c… | Indexed document abc123 (120 pages, 450 chunks)
  ```

---

## 2. Request-ID flow

1. A request arrives. `RequestLoggingMiddleware` checks for an incoming
   `X-Request-ID` header (reused for cross-service tracing, length-capped to
   128 chars since headers are untrusted); otherwise it mints a UUID4.
2. The ID is stored via `set_request_id()` in a `ContextVar`, so it is
   automatically visible to all code executed while the request is being
   processed — services, agents, LLM providers, DB access — without threading
   it through function signatures.
3. `RequestIDFilter` copies it onto every `LogRecord`, so the file format's
   `request_id=%(request_id)s` field is always populated (`-` outside any
   request, e.g. startup/shutdown logs).
4. The response carries the ID back to the client in the `X-Request-ID`
   header, so a user-reported problem can be matched to exact log lines.
5. **Background jobs** (PDF ingestion via `app/services/job_store.py`) run in
   a worker thread outside any request, so they call `bind_request_id(job_id)`
   to make all their logs correlatable by job ID instead.

---

## 3. What is logged

| Area | Events | Typical fields |
|---|---|---|
| HTTP requests | every request + response | method, path, status, duration (ms), request ID |
| Errors | all exceptions via global handlers and `logger.exception` | exception class, error code, endpoint, status, request ID; full traceback server-side only |
| Authentication | register, login success/failure, token rejection (401 via handler) | user ID (when known), failure reason (`unknown_user` / `bad_credentials` / `inactive`) |
| Rate limiting | backend choice, Redis connect/fallback, per-check failures, **429 denials** | identifier (user ID / client IP), endpoint, limit counts, retry-after, backend type |
| Retrieval | per-query timing (DEBUG) | duration (ms), chunk count, whether scoped to document/owner/temporal — never the query text |
| LLM calls | success/failure, retries | model, operation (`generate`/`stream`), duration, token counts, error type, retry attempt/delay |
| Document ingestion / background jobs | job start/complete/fail, indexing result | job ID (as request ID), document ID, page/chunk/table counts, duration, error type |
| PostgreSQL / Redis | health-check failures, connection fallbacks | backend, host/port (Redis) or backend type only (DB), error type, error text |
| Financial data providers | fetch success/failure | provider (`yahoo`), ticker, duration, error type |

Log levels used: `DEBUG` diagnostics, `INFO` successful operations,
`WARNING` degraded/recoverable conditions (Redis fallback, retries, failed
logins), `ERROR` failed operations with `exc_info`.

## 4. What is intentionally NEVER logged

- **Passwords** (plaintext or hashes) and login form contents.
- **API keys / secrets**: `OPENAI_API_KEY`, `FMP_API_KEY`, `SEC_API_KEY`,
  `AUTH_SECRET_KEY`, `EDGAR_IDENTITY`, DB passwords.
- **JWTs / bearer tokens** — token validation failures report the outcome,
  never the token value.
- **Database / Redis connection URLs** — they embed credentials; only
  backend type or host:port are reported.
- **Full user content** — chat prompts, LLM prompts/completions, streaming
  tokens and search queries are never logged; failures report a failure type
  (plus, where already established in the codebase, at most a short
  length-bounded query reference).
- **Financial figures and document contents** — statement values, market
  payloads, chunk text, and full documents are business data, not diagnostics.
- **Email addresses** in auth logs (user IDs only).

Sanitization already enforced elsewhere: the sandbox worker strips secret
environment variables (see `app/sandbox`), and `SecretStr` fields keep keys
out of accidental `repr()` output.

---

## 5. Configuration

All logging configuration comes from the existing `Settings` (`.env`), no new
infrastructure:

| Variable | Default | Meaning |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Root level: `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`. |
| `LOG_TO_CONSOLE` | `true` | Rich console output. |
| `LOG_TO_FILE` | `true` | Rotating file output under `storage/logs/`. |

Rotation constants (`LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`) live in
`app/core/constants.py`. Third-party libraries (`httpx`, `openai`, `urllib3`,
…) are capped at `WARNING` to keep the file readable. `setup_logging()` is
idempotent; tests can call it with `force=True`.

## 6. Health vs. readiness

| Endpoint | Purpose | Checks |
|---|---|---|
| `GET /health` | Liveness / component status (no heavy I/O) | application, configuration (API-key presence only, never the key), logging configured |
| `GET /readiness` | Deep infrastructure probe for orchestrators | real `SELECT 1` against the database, vector-store heartbeat, Redis `PING` (reported but never fails readiness — Redis is optional with database fallback). Returns **503** when a critical component is down; a failing probe is logged at `WARNING` with component states and duration. |

Both are public (no auth) and safe for load balancers / Kubernetes probes.

## 7. Adding logs to new code

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("Operation completed: operation=%s duration_ms=%.0f", op, ms)
logger.warning("Retryable failure: error_type=%s", exc.__class__.__name__)
logger.exception("Operation failed: entity_id=%s", entity_id)
```

Rules of thumb: lazy `%`-formatting (never f-strings in log calls), include
operation + duration + a safe identifier (request/job/document ID, ticker,
user ID), never include secrets or user/business content, and prefer
`error_type` + short `error` text over full exception payloads.
