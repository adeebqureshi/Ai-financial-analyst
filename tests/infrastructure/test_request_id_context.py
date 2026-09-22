import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.middleware.request_logging import RequestLoggingMiddleware
from app.core.logging import RequestIDFilter, setup_logging
from app.infrastructure.request_id import (
    bind_request_id,
    get_request_id,
)
def _make_record_with_filter() -> logging.LogRecord:
    setup_logging(force=True)
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="hello", args=(), exc_info=None,
    )
    RequestIDFilter().filter(record)
    return record
def test_default_request_id_is_placeholder():
    bind_request_id(None)
    record = _make_record_with_filter()
    assert record.request_id == get_request_id()
    assert record.request_id != "-"
def test_bound_job_id_appears_in_log_records():
    record = None
    job_id = bind_request_id("job123")
    record = _make_record_with_filter()
    assert record.request_id == job_id == "job123"
def test_middleware_stamps_request_id_header():
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
    @app.get("/ping")
    def ping():
        return {"request_id": get_request_id()}
    client = TestClient(app)
    response = client.get("/ping")
    header_id = response.headers["X-Request-ID"]
    assert header_id and len(header_id) >= 32
    assert response.json()["request_id"] == header_id
    response = client.get("/ping", headers={"X-Request-ID": "trace-abc"})
    assert response.headers["X-Request-ID"] == "trace-abc"