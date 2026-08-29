"""
Persistence / ownership / concurrency tests for the chat store.

These tests exercise ``ChatStore`` directly against a real (temporary) SQLite
database so they validate actual persistence behaviour rather than mocks.
"""

from __future__ import annotations

import threading
from datetime import timedelta

import pytest

from app.chat.database import get_db_session
from app.chat.models import _utcnow_naive
from app.chat.store import ChatStore


@pytest.fixture()
def store(tmp_path):
    return ChatStore(f"sqlite:///{tmp_path / 'chat.db'}")


def _save(store, owner, session_id, idx=0, answer="answer"):
    store.save_turn(
        owner,
        session_id,
        user_message=f"query-{idx}",
        assistant_message=f"{answer}-{idx}",
        user_meta={"ticker": "AAPL"},
        assistant_meta={"tickers": ["AAPL"], "query": f"query-{idx}", "answer": f"{answer}-{idx}"},
    )


def test_save_and_read_turn(store):
    store.save_turn(
        "user-a",
        "s1",
        user_message="What is Apple's price?",
        assistant_message="AAPL trades at $220.",
        user_meta={"ticker": "AAPL"},
        assistant_meta={"tickers": ["AAPL"], "query": "What is Apple's price?", "answer": "AAPL trades at $220."},
    )

    sessions, total = store.list_sessions("user-a")
    assert total == 1
    assert sessions[0]["session_id"] == "s1"
    assert sessions[0]["created_at"] is not None
    assert sessions[0]["updated_at"] is not None

    messages, mtotal = store.list_messages("user-a", "s1")
    assert mtotal == 2
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "What is Apple's price?"
    assert messages[1]["content"] == "AAPL trades at $220."
    assert messages[1]["metadata"]["tickers"] == ["AAPL"]


def test_session_is_lazy_and_reused_across_turns(store):
    _save(store, "user-a", "s1", 0, "first")
    _save(store, "user-a", "s1", 1, "second")

    sessions, total = store.list_sessions("user-a")
    assert total == 1

    _, mtotal = store.list_messages("user-a", "s1")
    assert mtotal == 4  # two turns x (user + assistant)

    state = store.get_session_state("user-a", "s1")
    assert state == {"tickers": ["AAPL"], "query": "query-1", "answer": "second-1"}


def test_ownership_isolation(store):
    _save(store, "user-a", "alice-session", 0)
    _save(store, "user-b", "bob-session", 0)

    # A only sees A's session.
    a_sessions, a_total = store.list_sessions("user-a")
    assert a_total == 1
    assert a_sessions[0]["session_id"] == "alice-session"

    b_sessions, b_total = store.list_sessions("user-b")
    assert b_total == 1
    assert b_sessions[0]["session_id"] == "bob-session"

    # B cannot read A's messages or state.
    b_messages, b_mtotal = store.list_messages("user-b", "alice-session")
    assert b_mtotal == 0
    assert b_messages == []
    assert store.get_session_state("user-b", "alice-session") is None

    # B cannot delete A's session.
    assert store.delete_session("user-b", "alice-session") is False
    # A's session is still intact.
    _, a_total = store.list_sessions("user-a")
    assert a_total == 1


def test_anonymous_owner_isolation(store):
    _save(store, None, "anon-session", 0)
    _save(store, "user-a", "user-session", 0)

    anon, anon_total = store.list_sessions(None)
    assert anon_total == 1
    assert anon[0]["session_id"] == "anon-session"

    user, user_total = store.list_sessions("user-a")
    assert user_total == 1
    assert user[0]["session_id"] == "user-session"

    assert store.get_session_state("user-a", "anon-session") is None


def test_pagination_newest_first(store):
    for i in range(25):
        _save(store, "user-a", f"session-{i:02d}", 0)

    first_page, total = store.list_sessions("user-a", page=1, page_size=10)
    assert total == 25
    assert len(first_page) == 10

    # updated_at desc => most recently written first.
    assert first_page[0]["session_id"] == "session-24"
    assert first_page[-1]["session_id"] == "session-15"

    last_page, _ = store.list_sessions("user-a", page=3, page_size=10)
    assert len(last_page) == 5
    assert last_page[-1]["session_id"] == "session-00"


def test_message_pagination_oldest_first(store):
    store.save_turn(
        "user-a",
        "s1",
        user_message="q",
        assistant_message="a",
        assistant_meta={"query": "q", "answer": "a"},
    )
    for i in range(5):
        store.save_turn(
            "user-a",
            "s1",
            user_message=f"q{i}",
            assistant_message=f"a{i}",
            assistant_meta={"query": f"q{i}", "answer": f"a{i}"},
        )

    page, total = store.list_messages("user-a", "s1", page=1, page_size=3)
    assert total == 12
    assert len(page) == 3
    assert page[0]["role"] == "user"
    assert page[0]["content"] == "q"
    assert page[-1]["content"] == "q0"


def test_delete_session_scoped_to_owner(store):
    _save(store, "user-a", "s-a", 0)
    _save(store, "user-b", "s-b", 0)

    assert store.delete_session("user-a", "s-a") is True
    _, a_total = store.list_sessions("user-a")
    assert a_total == 0
    assert store.get_session_state("user-a", "s-a") is None

    # B's session is unaffected.
    _, b_total = store.list_sessions("user-b")
    assert b_total == 1


def test_retention_cleanup_purges_idle_sessions(store, tmp_path):
    _save(store, "user-a", "old", 0)
    _save(store, "user-a", "fresh", 0)

    a_sessions, total = store.list_sessions("user-a")
    assert total == 2

    # Backdate the "old" session's last-activity timestamp.
    db_url = f"sqlite:///{tmp_path / 'chat.db'}"
    db_gen = get_db_session(db_url)
    db = next(db_gen)
    try:
        from app.chat.models import ChatSession

        old = db.query(ChatSession).filter_by(session_id="old").one()
        old.updated_at = _utcnow_naive() - timedelta(days=400)
        db.commit()
    finally:
        db.close()

    store2 = ChatStore(db_url, retention_days=30)
    removed = store2.purge_expired()
    assert removed == 1

    sessions, total = store2.list_sessions("user-a")
    assert total == 1
    assert sessions[0]["session_id"] == "fresh"

    # Orphaned messages were removed too.
    assert store2.get_session_state("user-a", "old") is None


def test_persisted_state_survives_a_restart(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'chat.db'}"

    store1 = ChatStore(db_url)
    _save(store1, "user-a", "s1", 0, "first")
    _save(store1, "user-a", "s1", 1, "second")

    # A brand-new store instance over the same file simulates a process restart.
    store2 = ChatStore(db_url)
    _, total = store2.list_sessions("user-a")
    assert total == 1

    _, mtotal = store2.list_messages("user-a", "s1")
    assert mtotal == 4

    state = store2.get_session_state("user-a", "s1")
    assert state == {"tickers": ["AAPL"], "query": "query-1", "answer": "second-1"}


def test_concurrent_get_or_create_creates_a_single_session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'chat.db'}"
    store = ChatStore(db_url)

    threads = 6
    errors: list[Exception] = []
    barrier = threading.Barrier(threads)

    def worker(idx: int) -> None:
        try:
            barrier.wait(timeout=10)
            _save(store, "user-a", "shared", idx)
        except Exception as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    worker_threads = [threading.Thread(target=worker, args=(i,)) for i in range(threads)]
    for t in worker_threads:
        t.start()
    for t in worker_threads:
        t.join(timeout=30)

    assert errors == []

    sessions, total = store.list_sessions("user-a")
    assert total == 1
    assert sessions[0]["session_id"] == "shared"

    _, mtotal = store.list_messages("user-a", "shared")
    assert mtotal == 2 * threads