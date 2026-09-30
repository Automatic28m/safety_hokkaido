from agent_core.context_manager import (
    MAX_TURNS_PER_CONVERSATION,
    ContextManager,
    ConversationMemory,
    ConversationMemoryStore,
    normalize_history,
    strip_trailing_query,
)
from agent_core.schemas import OrchestrationRequest
from conftest import FakeLLM


def test_normalize_history_maps_ai_and_drops_other_roles():
    history = [
        {"role": "ai", "content": "hello"},
        {"role": "system", "content": "secret"},
        {"role": "tool", "content": "x"},
        {"role": "user", "content": "   "},
        {"role": "user", "content": "hi"},
        "junk",
    ]
    assert normalize_history(history) == [
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "hi"},
    ]


def test_strip_trailing_query_removes_duplicate_current_turn():
    history = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}, {"role": "user", "content": "q"}]
    assert strip_trailing_query(history, "q ") == history[:2]
    assert strip_trailing_query(history[:2], "q") == history[:2]


def test_two_conversations_never_share_history():
    store = ConversationMemoryStore()
    store.get("conv-a").add_turn("user", "I am trapped in Otaru")
    store.get("conv-b").add_turn("user", "Sapporo weather?")
    assert [t["content"] for t in store.get("conv-a").get_history()] == ["I am trapped in Otaru"]
    assert [t["content"] for t in store.get("conv-b").get_history()] == ["Sapporo weather?"]
    store.clear("conv-a")
    assert store.get("conv-a", create=False) is None
    assert store.get("conv-b", create=False) is not None


def test_store_evicts_oldest_conversation():
    store = ConversationMemoryStore(max_conversations=2)
    store.get("1"), store.get("2"), store.get("3")
    assert store.get("1", create=False) is None and len(store) == 2


def test_api_history_is_authoritative_over_memory():
    store = ConversationMemoryStore()
    store.get("conv").add_turn("user", "server-side memory turn")
    ctx = ContextManager(llm_client=FakeLLM(), store=store, model="m", use_memory=True)
    request = OrchestrationRequest(
        request_id="r",
        conversation_id="conv",
        original_query="current",
        chat_history=[{"role": "user", "content": "from api"}, {"role": "user", "content": "current"}],
    )
    history, source = ctx.resolve_history(request)
    assert source == "api"
    assert history == [{"role": "user", "content": "from api"}]


def test_memory_used_only_when_api_history_absent_and_conversation_known():
    store = ConversationMemoryStore()
    store.get("conv").add_turn("user", "earlier")
    ctx = ContextManager(llm_client=FakeLLM(), store=store, model="m", use_memory=True)
    known = OrchestrationRequest(request_id="r", conversation_id="conv", original_query="now")
    assert ctx.resolve_history(known) == ([{"role": "user", "content": "earlier"}], "memory")
    other = OrchestrationRequest(request_id="r", conversation_id="someone-else", original_query="now")
    assert ctx.resolve_history(other) == ([], "none")
    anonymous = OrchestrationRequest(request_id="r", original_query="now")
    assert ctx.resolve_history(anonymous) == ([], "none")


def test_remember_requires_conversation_id_and_memory_toggle():
    store = ConversationMemoryStore()
    ctx = ContextManager(llm_client=FakeLLM(), store=store, model="m", use_memory=True)
    ctx.remember(OrchestrationRequest(request_id="r", original_query="q"), "reply")
    assert len(store) == 0
    ctx.remember(OrchestrationRequest(request_id="r", conversation_id="c", original_query="q"), "reply")
    assert [t["role"] for t in store.get("c").get_history()] == ["user", "assistant"]

    off = ContextManager(llm_client=FakeLLM(), store=ConversationMemoryStore(), model="m", use_memory=False)
    off.remember(OrchestrationRequest(request_id="r", conversation_id="c", original_query="q"), "reply")
    assert len(off.store) == 0


def test_memory_summarizes_long_history_with_summarizer():
    memory = ConversationMemory(summarize=lambda turns: f"{len(turns)} old turns")
    for i in range(MAX_TURNS_PER_CONVERSATION + 1):
        memory.add_turn("user" if i % 2 == 0 else "assistant", f"turn {i}")
    history = memory.get_history()
    assert history[0]["content"].startswith("[Earlier conversation summary:")
    assert len(history) == 1 + 4


def test_reformulate_and_translate_keep_original_on_failure():
    ctx = ContextManager(llm_client=FakeLLM(fail_on={"reformulate", "translate"}), store=ConversationMemoryStore(), model="m")
    standalone, notice = ctx.reformulate_query("and Otaru?", [{"role": "user", "content": "weather in Sapporo"}])
    assert standalone == "and Otaru?" and notice
    english, notice = ctx.translate_for_retrieval("หิมะตกไหม", "th")
    assert english == "หิมะตกไหม" and notice


def test_translate_skips_english_and_reformulate_skips_without_history():
    llm = FakeLLM()
    ctx = ContextManager(llm_client=llm, store=ConversationMemoryStore(), model="m")
    assert ctx.translate_for_retrieval("snow?", "en") == ("snow?", None)
    assert ctx.reformulate_query("snow?", []) == ("snow?", None)
    assert llm.calls == []
    assert ctx.translate_for_retrieval("หิมะ", "th") == ("english retrieval query", None)


def test_build_context_package_windows_history():
    request = OrchestrationRequest(request_id="r", original_query="q")
    history = [{"role": "user", "content": str(i)} for i in range(10)]
    package = ContextManager.build_context_package(request, history, [], [], "en", {"route": "general"}, "general")
    assert len(package.history) == 6 and package.history[-1]["content"] == "9"
