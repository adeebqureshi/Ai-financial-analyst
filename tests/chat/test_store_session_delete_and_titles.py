"""Store-level guarantees behind the delete affordance.

Focused on two things the HTTP layer relies on: deletion is precisely scoped,
and a session gets a real, non-fabricated title derived from what the user
actually asked.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.chat.models import ChatMessage, ChatSession
from app.chat.store import ChatStore, _title_from_message


@pytest.fixture()
def store(tmp_path):
    return ChatStore(f"sqlite:///{tmp_path / 'chat.db'}")


def _save(store: ChatStore, owner, session_id, question: str, answer: str = "ok") -> None:
    store.save_turn(
        owner,
        session_id,
        user_message=question,
        assistant_message=answer,
        user_meta={"ticker": None},
        assistant_meta={"query": question, "answer": answer, "tickers": []},
    )


def _row_counts(store: ChatStore) -> tuple[int, int]:
    with store._session() as db:  # noqa: SLF001 - test-only introspection
        sessions = db.scalar(select(func.count(ChatSession.id)))
        messages = db.scalar(select(func.count(ChatMessage.id)))
        return int(sessions or 0), int(messages or 0)


# --- deletion is precisely scoped ------------------------------------------


def test_delete_removes_only_the_targeted_session(store):
    _save(store, "user-a", "keep", "Keep me")
    _save(store, "user-a", "drop", "Drop me")
    _save(store, "user-a", "also-keep", "Keep me too")

    assert store.delete_session("user-a", "drop") is True

    assert store.get_session("user-a", "drop") is None
    remaining, total = store.list_sessions("user-a")
    assert total == 2
    assert {row["session_id"] for row in remaining} == {"keep", "also-keep"}
    # 2 surviving sessions x (1 user + 1 assistant) message each.
    assert _row_counts(store) == (2, 4)


def test_delete_takes_the_messages_with_it(store):
    _save(store, "user-a", "chatty", "First question")
    _save(store, "user-a", "chatty", "Second question")
    _save(store, "user-a", "chatty", "Third question")
    assert _row_counts(store) == (1, 6)

    assert store.delete_session("user-a", "chatty") is True

    # No orphaned message rows survive the session.
    assert _row_counts(store) == (0, 0)
    messages, total = store.list_messages("user-a", "chatty")
    assert total == 0
    assert messages == []


def test_delete_is_a_no_op_for_an_unknown_session(store):
    _save(store, "user-a", "s1", "Question")
    assert store.delete_session("user-a", "does-not-exist") is False
    assert _row_counts(store) == (1, 2)


def test_delete_cannot_reach_another_owners_session(store):
    _save(store, "user-a", "alice-s", "Alice")
    _save(store, "user-b", "bob-s", "Bob")

    assert store.delete_session("user-b", "alice-s") is False
    assert store.get_session("user-a", "alice-s") is not None
    assert _row_counts(store) == (2, 4)

    assert store.delete_session("user-a", "alice-s") is True
    assert store.get_session("user-b", "bob-s") is not None
    assert _row_counts(store) == (1, 2)


def test_anonymous_owner_cannot_delete_a_users_session(store):
    _save(store, "user-a", "user-s", "Question")
    _save(store, None, "anon-s", "Question")

    assert store.delete_session(None, "user-s") is False
    assert store.delete_session("user-a", "anon-s") is False
    assert _row_counts(store) == (2, 4)


# --- titles come from real data --------------------------------------------


def test_title_falls_back_to_the_first_user_question(store):
    _save(store, "user-a", "s1", "What was the revenue growth this year?")
    _save(store, "user-a", "s1", "And margins?")

    rows, _ = store.list_sessions("user-a")
    # Derived on read, so this must be the *first* question, not the latest.
    assert rows[0]["title"] == "What was the revenue growth this year?"


def test_title_uses_the_first_question_across_owners_independently(store):
    _save(store, "user-a", "shared-id", "Alice question")
    _save(store, "user-b", "shared-id", "Bob question")

    a_rows, _ = store.list_sessions("user-a")
    b_rows, _ = store.list_sessions("user-b")
    assert a_rows[0]["title"] == "Alice question"
    assert b_rows[0]["title"] == "Bob question"


def test_explicit_title_is_never_overwritten(store):
    store.save_turn(
        "user-a",
        "s1",
        user_message="A later question",
        assistant_message="ok",
        title="Curated title",
    )

    rows, _ = store.list_sessions("user-a")
    assert rows[0]["title"] == "Curated title"


def test_titled_sessions_are_not_given_a_derived_one(store):
    store.save_turn(
        "user-a",
        "titled",
        user_message="Question text",
        assistant_message="ok",
        title="Real title",
    )
    _save(store, "user-a", "untitled", "Fallback question")

    rows, _ = store.list_sessions("user-a")
    by_id = {row["session_id"]: row["title"] for row in rows}
    assert by_id["titled"] == "Real title"
    assert by_id["untitled"] == "Fallback question"


def test_session_with_no_user_message_has_no_invented_title(store):
    # A session row that never received a user message must stay untitled rather
    # than get a placeholder string.
    store.save_turn(
        "user-a",
        "assistant-only",
        user_message="   ",
        assistant_message="ok",
    )
    rows, total = store.list_sessions("user-a")
    assert total == 1
    assert rows[0]["title"] in (None, "")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", ""),
        ("   ", ""),
        ("\n\t", ""),
        ("short question", "short question"),
        ("multi\n  line   paste", "multi line paste"),
        ("  padded  ", "padded"),
    ],
)
def test_title_helper_collapses_whitespace(raw, expected):
    assert _title_from_message(raw) == expected


def test_title_helper_truncates_on_a_word_boundary():
    title = _title_from_message("word " * 40)
    assert len(title) <= 80
    assert title.endswith("…")
    # Never a lone dangling character where a word was cut in half.
    assert not title[:-1].endswith("wor")