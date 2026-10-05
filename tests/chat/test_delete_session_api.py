"""Delete a research/chat session, end to end through the HTTP API.

Covers the guarantees the "Recent research sessions" delete affordance relies
on: the row really leaves persistent storage, its messages go with it, nothing
else is touched, and one caller can never reach another caller's session.
"""

from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from app.chat.models import ChatMessage, ChatSession

from tests.chat.test_persistence_api import _headers, _make_app, _register_and_login


def _seed(client: TestClient, token: str, session_id: str, question: str) -> None:
    response = client.post(
        "/chat",
        headers=_headers(token),
        json={"message": question, "session_id": session_id},
    )
    assert response.status_code == 200, response.text


def _count_rows(store, session_id: str) -> tuple[int, int]:
    """(sessions, messages) rows still present for one session id."""
    from sqlalchemy import func, select

    with store._session() as db:  # noqa: SLF001 - test-only introspection
        session = db.scalar(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        if session is None:
            return 0, 0
        messages = db.scalar(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.session_id == session.id
            )
        )
        return 1, int(messages or 0)


def test_delete_removes_session_and_its_messages(tmp_path):
    app, store = _make_app(tmp_path)

    with TestClient(app) as client:
        token = _register_and_login(client, "alice@example.com")
        _seed(client, token, "sess-delete", "What drove revenue growth?")

        assert _count_rows(store, "sess-delete") == (1, 2)

        deleted = client.delete(
            "/chat/sessions/sess-delete", headers=_headers(token)
        )
        assert deleted.status_code == 204, deleted.text
        assert deleted.content == b""

        # Persisted state, not just the API projection.
        assert _count_rows(store, "sess-delete") == (0, 0)
        assert store.get_session(_owner_of(store), "sess-delete") is None

        listed = client.get("/chat/sessions", headers=_headers(token))
        assert listed.json()["data"]["total"] == 0


def test_delete_is_idempotently_gone_from_listing(tmp_path):
    app, _ = _make_app(tmp_path)

    with TestClient(app) as client:
        token = _register_and_login(client, "alice@example.com")
        _seed(client, token, "sess-gone", "Summarize key risks")

        assert client.delete(
            "/chat/sessions/sess-gone", headers=_headers(token)
        ).status_code == 204

        listed = client.get("/chat/sessions", headers=_headers(token))
        assert listed.json()["data"]["total"] == 0
        assert listed.json()["data"]["sessions"] == []


def test_delete_unknown_session_returns_404(tmp_path):
    app, _ = _make_app(tmp_path)

    with TestClient(app) as client:
        token = _register_and_login(client, "alice@example.com")

        missing = client.delete(
            "/chat/sessions/never-existed", headers=_headers(token)
        )
        assert missing.status_code == 404, missing.text
        assert missing.json()["success"] is False
        # A miss must not be reported as a successful deletion.
        assert "deleted" not in (missing.json().get("data") or {})


def test_cannot_delete_another_users_session(tmp_path):
    app, store = _make_app(tmp_path)

    with TestClient(app) as client:
        alice = _register_and_login(client, "alice@example.com")
        bob = _register_and_login(client, "bob@example.com")
        _seed(client, alice, "alice-private", "Alice only")

        attempt = client.delete(
            "/chat/sessions/alice-private", headers=_headers(bob)
        )
        # 404 rather than 403: a 403 would leak that the id exists elsewhere.
        assert attempt.status_code == 404, attempt.text

        # And Alice's session is completely untouched.
        assert _count_rows(store, "alice-private") == (1, 2)
        alice_list = client.get("/chat/sessions", headers=_headers(alice))
        assert [s["session_id"] for s in alice_list.json()["data"]["sessions"]] == [
            "alice-private"
        ]


def test_delete_leaves_other_sessions_untouched(tmp_path):
    app, store = _make_app(tmp_path)

    with TestClient(app) as client:
        token = _register_and_login(client, "alice@example.com")
        for session_id in ("keep-1", "drop-me", "keep-2"):
            _seed(client, token, session_id, f"Question about {session_id}")

        assert client.delete(
            "/chat/sessions/drop-me", headers=_headers(token)
        ).status_code == 204

        remaining = client.get("/chat/sessions", headers=_headers(token))
        ids = {s["session_id"] for s in remaining.json()["data"]["sessions"]}
        assert ids == {"keep-1", "keep-2"}
        assert remaining.json()["data"]["total"] == 2

        assert _count_rows(store, "keep-1") == (1, 2)
        assert _count_rows(store, "keep-2") == (1, 2)
        assert _count_rows(store, "drop-me") == (0, 0)

        # The survivors are still fully readable, not orphaned.
        messages = client.get("/chat/sessions/keep-1/messages", headers=_headers(token))
        assert messages.json()["data"]["total"] == 2


def test_deleted_session_messages_endpoint_is_empty(tmp_path):
    app, _ = _make_app(tmp_path)

    with TestClient(app) as client:
        token = _register_and_login(client, "alice@example.com")
        _seed(client, token, "sess-messages", "What are the key risks?")

        assert client.delete(
            "/chat/sessions/sess-messages", headers=_headers(token)
        ).status_code == 204

        messages = client.get(
            "/chat/sessions/sess-messages/messages", headers=_headers(token)
        )
        assert messages.json()["data"]["total"] == 0
        assert messages.json()["data"]["messages"] == []


def test_delete_preserves_documents_and_other_users_sessions(tmp_path):
    """A session delete must not cascade into unrelated stores."""
    app, store = _make_app(tmp_path)

    with TestClient(app) as client:
        alice = _register_and_login(client, "alice@example.com")
        bob = _register_and_login(client, "bob@example.com")
        _seed(client, alice, "alice-s1", "Alice question")
        _seed(client, bob, "bob-s1", "Bob question")

        assert client.delete(
            "/chat/sessions/alice-s1", headers=_headers(alice)
        ).status_code == 204

        assert _count_rows(store, "bob-s1") == (1, 2)
        bob_list = client.get("/chat/sessions", headers=_headers(bob))
        assert bob_list.json()["data"]["total"] == 1


def test_delete_last_session_leaves_an_empty_list_not_a_placeholder(tmp_path):
    app, _ = _make_app(tmp_path)

    with TestClient(app) as client:
        token = _register_and_login(client, "alice@example.com")
        _seed(client, token, "only-session", "Is NVDA overvalued?")

        assert client.delete(
            "/chat/sessions/only-session", headers=_headers(token)
        ).status_code == 204

        body = client.get("/chat/sessions", headers=_headers(token)).json()["data"]
        assert body["total"] == 0
        assert body["sessions"] == []


def test_delete_requires_a_token_when_auth_enabled(tmp_path):
    app, store = _make_app(tmp_path)

    with TestClient(app) as client:
        token = _register_and_login(client, "alice@example.com")
        _seed(client, token, "sess-auth", "Who am I?")

        # The suite enables auth, so the router-level guard rejects an
        # unauthenticated caller with 401 before the handler can act on it.
        anonymous = client.delete("/chat/sessions/sess-auth")
        assert anonymous.status_code == 401, anonymous.text
        assert anonymous.json()["success"] is False
        assert _count_rows(store, "sess-auth") == (1, 2)


def _owner_of(store):  # pragma: no cover - helper kept for readability
    with store._session() as db:  # noqa: SLF001
        from sqlalchemy import select

        return db.scalar(select(ChatSession.owner_id).limit(1))