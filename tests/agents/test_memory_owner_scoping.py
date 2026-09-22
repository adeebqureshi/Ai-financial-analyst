from app.agents.memory import ConversationMemory
def test_same_session_id_different_owners_are_isolated():
    memory = ConversationMemory()
    memory.remember("shared-session", ["AAPL"], "Analyze Apple.", "Apple is...", owner_id="user-a")
    memory.remember("shared-session", ["MSFT"], "Analyze Microsoft.", "Microsoft is...", owner_id="user-b")
    a = memory.recall("shared-session", owner_id="user-a")
    b = memory.recall("shared-session", owner_id="user-b")
    assert a is not None and a["tickers"] == ["AAPL"]
    assert b is not None and b["tickers"] == ["MSFT"]
def test_owner_scope_prevents_followup_leak():
    memory = ConversationMemory()
    memory.remember("s1", ["AAPL"], "Analyze Apple.", "ok", owner_id="user-a")
    assert memory.recall("s1", owner_id="user-b") is None
    assert memory.resolve_tickers("What is the revenue?", [], "s1", owner_id="user-b") == []
    assert memory.resolve_tickers("What is the revenue?", [], "s1", owner_id="user-a") == ["AAPL"]
def test_hydration_restores_context_after_cache_miss():
    planner_memory = ConversationMemory()
    planner_memory.remember("s1", ["AAPL"], "Analyze Apple.", "ok", owner_id="user-a")
    restored = ConversationMemory()
    restored.remember("s1", ["AAPL"], "Analyze Apple.", "ok", owner_id="user-a")
    assert restored.recall("s1", owner_id="user-a")["tickers"] == ["AAPL"]
    assert planner_memory.recall("s1", owner_id="user-a")["tickers"] == ["AAPL"]
def test_anonymous_owner_is_its_own_scope():
    memory = ConversationMemory()
    memory.remember("anon-session", ["AAPL"], "Analyze Apple.", "ok")
    memory.remember("anon-session", ["TSLA"], "Analyze Tesla.", "ok", owner_id=None)
    assert memory.recall("anon-session")["tickers"] == ["TSLA"]
    assert memory.recall("anon-session", owner_id="user-a") is None
def test_eviction_and_ttl_still_scoped():
    memory = ConversationMemory()
    memory.remember("s", ["AAPL"], "q", "a", owner_id="user-a")
    memory.remember("s", ["MSFT"], "q", "a", owner_id="user-b")
    assert memory.recall("s", owner_id="user-a")["tickers"] == ["AAPL"]
    assert memory.recall("s", owner_id="user-b")["tickers"] == ["MSFT"]
    assert memory.recall("s", owner_id="user-c") is None