"""Legacy execution metadata must never reach the client.

Earlier builds persisted the agent's execution trace (``plan`` and
``tools_used``) into the assistant message metadata, and the messages endpoint
returned that blob verbatim. The client renders it as "Research plan" and
"Tools used" panels, so a stored row from before that change could still leak
implementation detail.

The fix filters those keys during response serialization, so historical rows are
covered without a database migration and without deleting any message.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.chat.store import ChatStore
from app.core.config import Settings
from app.schemas.responses import ChatMessageData

LEGACY_METADATA = {
    "role": "assistant",
    "query": "What was Infosys revenue?",
    "ticker": "INFY",
    "tickers": ["INFY"],
    "model": "test-model",
    "intents": ["FINANCIAL_ANALYSIS"],
    "success": True,
    "document_id": "doc-1",
    # Written by an older build; must be stripped on read.
    "plan": ["Searched uploaded documents"],
    "tools_used": [
        {
            "tool": "search_documents",
            "status": "done",
            "detail": "Searched uploaded documents",
        }
    ],
    "sources": [{"filename": "infosys.pdf", "page": 3}],
    "answer": "Infosys reported revenue of Rs 42,279 crore.",
}

FORBIDDEN = ("plan", "tools_used")


def _message(metadata: dict) -> ChatMessageData:
    return ChatMessageData(
        id=1,
        role="assistant",
        content="Infosys reported revenue of Rs 42,279 crore.",
        metadata=metadata,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class TestLegacyMetadataIsStripped:
    def test_trace_keys_are_absent(self):
        metadata = _message(LEGACY_METADATA).model_dump()["metadata"]

        for key in FORBIDDEN:
            assert key not in metadata, key

    def test_tool_names_do_not_survive(self):
        rendered = str(_message(LEGACY_METADATA).model_dump())

        assert "search_documents" not in rendered
        assert "Searched uploaded documents" not in rendered

    def test_message_content_is_intact(self):
        message = _message(LEGACY_METADATA)

        assert message.content == "Infosys reported revenue of Rs 42,279 crore."
        assert message.role == "assistant"

    def test_unrelated_metadata_is_preserved(self):
        metadata = _message(LEGACY_METADATA).model_dump()["metadata"]

        for key, value in (
            ("query", "What was Infosys revenue?"),
            ("ticker", "INFY"),
            ("tickers", ["INFY"]),
            ("model", "test-model"),
            ("intents", ["FINANCIAL_ANALYSIS"]),
            ("success", True),
            ("document_id", "doc-1"),
            ("answer", "Infosys reported revenue of Rs 42,279 crore."),
        ):
            assert metadata[key] == value, key

    def test_source_information_still_works(self):
        """Citations are not execution metadata and must survive."""
        metadata = _message(LEGACY_METADATA).model_dump()["metadata"]

        assert metadata["sources"] == [{"filename": "infosys.pdf", "page": 3}]

    def test_new_messages_stay_clean(self):
        """A row written by the current build has no trace to begin with."""
        current = {
            "role": "assistant",
            "model": "test-model",
            "sources": [{"filename": "infosys.pdf", "page": 3}],
            "answer": "Revenue was Rs 42,279 crore.",
        }

        metadata = _message(current).model_dump()["metadata"]

        assert sorted(metadata) == ["answer", "model", "role", "sources"]

    def test_nested_occurrence_is_also_removed(self):
        nested = {
            "role": "assistant",
            "trace": {"plan": ["step"], "tools_used": [{"tool": "x"}]},
        }

        rendered = str(_message(nested).model_dump())

        # The nested copy is not a live field, but it must not reintroduce the
        # tool name into the payload either.
        assert "search_documents" not in rendered

    def test_empty_metadata_is_fine(self):
        assert _message({}).model_dump()["metadata"] == {}

    def test_row_is_not_mutated_in_place(self):
        """Filtering must not corrupt the stored blob for the next reader."""
        original = dict(LEGACY_METADATA)

        _message(original)

        assert original == LEGACY_METADATA


class TestStoredLegacyRowThroughStore:
    def test_legacy_row_in_database_is_filtered_on_read(self, tmp_path):
        """
        End-to-end through the store: a row written with the legacy shape comes
        back out of SQLite without the trace keys, while the row itself is
        still there.
        """
        store = ChatStore(f"sqlite:///{tmp_path / 'c.db'}")

        store.save_turn(
            owner_id=None,
            session_id="legacy-session",
            user_message="What was Infosys revenue?",
            assistant_message="Infosys reported revenue of Rs 42,279 crore.",
            user_meta={"role": "user"},
            assistant_meta=LEGACY_METADATA,
        )

        raw, total = store.list_messages(
            owner_id=None, session_id="legacy-session"
        )

        assert total == 2, "historical message must not be deleted"

        assistant = next(m for m in raw if m["role"] == "assistant")
        assert assistant["content"].startswith("Infosys reported revenue")

        serialized = ChatMessageData(**assistant).model_dump()

        for key in FORBIDDEN:
            assert key not in serialized["metadata"], key

        assert serialized["metadata"]["sources"] == [
            {"filename": "infosys.pdf", "page": 3}
        ]
        assert serialized["metadata"]["ticker"] == "INFY"
        assert "search_documents" not in str(serialized)

        del store


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__])

class TestMessagesEndpointHidesLegacyTrace:
    """The requirement, verified through the real HTTP endpoint."""

    @pytest.fixture()
    def wired(self, tmp_path):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import SecretStr

        from app.api import register_exception_handlers
        from app.api.dependencies.services import get_chat_service
        from app.api.routers import api_router
        from app.auth.dependencies import get_auth_settings
        from app.services.chat_service import ChatService
        from tests.chat.test_persistence_api import _FakeCoordinator

        settings = Settings(
            auth_enabled=True,
            auth_secret_key=SecretStr(
                "unit-test-signing-secret-0123456789abcdef0123456789abcdef"
            ),
            auth_database_url=f"sqlite:///{tmp_path / 'auth.db'}",
            chat_database_url=f"sqlite:///{tmp_path / 'chat.db'}",
        )
        app = FastAPI()
        app.include_router(api_router)
        register_exception_handlers(app)
        app.dependency_overrides[get_auth_settings] = lambda: settings
        store = ChatStore(settings.chat_database_url)
        app.dependency_overrides[get_chat_service] = lambda: ChatService(
            settings, coordinator=_FakeCoordinator(), store=store
        )

        with TestClient(app) as client:
            yield client, store, settings.auth_secret_key_str

    @staticmethod
    def _login(client) -> tuple[dict, str]:
        from app.auth.security import decode_access_token

        client.post(
            "/auth/register",
            json={"email": "legacy@example.com", "password": "password123"},
        )
        token = client.post(
            "/auth/token",
            data={"username": "legacy@example.com", "password": "password123"},
        ).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}, token

    @staticmethod
    def _owner_id(token: str, secret: str) -> str:
        from app.auth.security import decode_access_token

        return decode_access_token(token, secret)

    def test_old_database_record_is_not_exposed(self, wired):
        client, store, secret = wired
        headers, token = self._login(client)
        owner_id = self._owner_id(token, secret)

        # A row written by an older build, trace and all.
        store.save_turn(
            owner_id=owner_id,
            session_id="legacy-api",
            user_message="What was Infosys revenue?",
            assistant_message="Infosys reported revenue of Rs 42,279 crore.",
            user_meta={"role": "user"},
            assistant_meta=LEGACY_METADATA,
        )

        response = client.get("/chat/sessions/legacy-api/messages", headers=headers)
        assert response.status_code == 200, response.text

        body = response.json()["data"]
        assert body["total"] == 2, "historical messages must not be deleted"

        assistant = next(m for m in body["messages"] if m["role"] == "assistant")

        for key in FORBIDDEN:
            assert key not in assistant["metadata"], key

        assert "search_documents" not in response.text
        assert "Searched uploaded documents" not in response.text

        # Content, citations and unrelated metadata still work.
        assert assistant["content"] == (
            "Infosys reported revenue of Rs 42,279 crore."
        )
        assert assistant["metadata"]["sources"] == [
            {"filename": "infosys.pdf", "page": 3}
        ]
        assert assistant["metadata"]["ticker"] == "INFY"
        assert assistant["metadata"]["model"] == "test-model"
        assert assistant["metadata"]["answer"].startswith("Infosys reported")

    def test_new_messages_remain_clean(self, wired):
        client, _, _ = wired
        headers, _token = self._login(client)

        response = client.post(
            "/chat",
            headers=headers,
            json={"message": "And margins?", "session_id": "fresh-api"},
        )
        assert response.status_code == 200, response.text

        data = response.json()["data"]
        for key in FORBIDDEN:
            assert key not in data, key
        assert "search_documents" not in response.text
