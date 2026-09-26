"""Regression tests for the issues found in the review of the first implementation."""
import json

from agent_core import guardrails
from agent_core.classifier import IntentClassifier, contains_keyword, detect_language
from agent_core.context_manager import ContextManager, ConversationMemoryStore
from agent_core.main import _coerce_decision
from agent_core.schemas import OrchestrationRequest
from conftest import DECISION_OK, FakeLLM, normalized_request


# --- classifier -----------------------------------------------------------------

def test_router_empty_tool_list_means_unknown_not_none():
    clf = IntentClassifier(llm_client=FakeLLM(route="realtime", confidence=0.9, tools=[]), model="m")
    decision = clf.classify_message("what is happening")
    assert decision.tool_hints is None


def test_router_tool_list_is_respected_when_given():
    clf = IntentClassifier(llm_client=FakeLLM(route="realtime", confidence=0.9, tools=["disaster"]), model="m")
    decision = clf.classify_message("what is happening")
    assert decision.tool_hints == ["disaster"]


def test_short_keywords_match_whole_words_only():
    assert contains_keyword("jr trains", "jr") and not contains_keyword("jrpass", "jr")
    assert contains_keyword("call 119", "119") and not contains_keyword("room 1190", "119")
    assert contains_keyword("it is windy", "windy") and not contains_keyword("close the window", "wind")
    assert contains_keyword("storms ahead", "storm")  # longer keywords still match at word start


def test_common_phrases_no_longer_trigger_realtime():
    assert IntentClassifier.keyword_route("I live in Sapporo") is None
    assert IntentClassifier.keyword_route("please close the window") is None
    assert IntentClassifier.keyword_route("is it safe  now") == "rag+realtime"  # extra spaces collapsed
    assert IntentClassifier.tool_hints("I bought a jrpass") == []


def test_detect_language_uses_locale_only_without_letters():
    assert detect_language("???", fallback="th") == "th"
    assert detect_language("hello", fallback="th") == "en"
    assert detect_language("", fallback="xx") == "en"


def test_extract_slots_prefers_first_city_in_text():
    assert IntentClassifier.extract_slots("driving from Otaru to Sapporo", None)["city"] == "Otaru"
    assert IntentClassifier.extract_slots("ขับจากซัปโปโรไปโอตารุ", None)["city"] == "Sapporo"


# --- decision coercion --------------------------------------------------------

def test_coerce_decision_normalizes_loose_model_output():
    coerced = _coerce_decision({"reply": "ok", "used_evidence_ids": None, "used_live_sources": [1, None], "degraded": "yes"})
    assert coerced["used_evidence_ids"] == [] and coerced["used_live_sources"] == ["1"]
    assert coerced["degraded"] is True and coerced["notices"] == [] and coerced["safety_level"] == "unknown"


def test_loose_decision_is_accepted_instead_of_503(build_agent):
    loose = dict(DECISION_OK, used_evidence_ids=None, used_live_sources=[7], notices=None)
    response = build_agent(llm=FakeLLM(decision=loose)).ask_structured(normalized_request("blizzard help"))
    assert response["status"] == "ok" and response["used_evidence_ids"] == []


# --- degraded semantics -------------------------------------------------------

def test_mocked_source_degrades_only_when_the_decision_relied_on_it(build_agent):
    relies = dict(DECISION_OK, used_live_sources=["jr_hokkaido_simulator"])
    response = build_agent(llm=FakeLLM(decision=relies)).ask_structured(normalized_request("Is the airport train delayed right now?"))
    assert response["degraded"] is True and "jr_hokkaido_simulator" in response["used_live_sources"]

    ignores = dict(DECISION_OK, used_live_sources=["meteosource"])
    response = build_agent(llm=FakeLLM(decision=ignores)).ask_structured(normalized_request("Is the airport train delayed right now?"))
    assert response["degraded"] is False


def test_missing_city_notice_comes_from_orchestrator(build_agent):
    response = build_agent(llm=FakeLLM(route="realtime", tools=["weather"])).ask_structured(normalized_request("Is it snowing right now?"))
    assert any("no city was mentioned" in n for n in response["notices"])


# --- guardrails ---------------------------------------------------------------

def test_long_reply_is_shortened_with_a_notice():
    result, notices = guardrails.validate_decision({"reply": "x" * 9000}, [], [], dependency_degraded=False)
    assert len(result.reply) == 8000
    assert any("shortened" in n for n in notices)


# --- memory -------------------------------------------------------------------

def test_api_history_rebuilds_memory_completely():
    store = ConversationMemoryStore()
    ctx = ContextManager(llm_client=FakeLLM(), store=store, model="m", use_memory=True)
    request = OrchestrationRequest(
        request_id="r",
        conversation_id="conv",
        original_query="and tonight?",
        chat_history=[{"role": "user", "content": "weather in Otaru"}, {"role": "assistant", "content": "snowy"}],
    )
    history, source = ctx.resolve_history(request)
    ctx.remember(request, "cold tonight", history=history, history_source=source)
    assert [t["content"] for t in store.get("conv").get_history()] == [
        "weather in Otaru", "snowy", "and tonight?", "cold tonight"
    ]


def test_store_summarizer_is_not_rebound_by_a_second_context_manager():
    store = ConversationMemoryStore()
    first = ContextManager(llm_client=FakeLLM(), store=store, model="m", use_memory=True)
    ContextManager(llm_client=FakeLLM(fail_on={"summarize"}), store=store, model="m", use_memory=True)
    assert store._summarizer == first.summarize_history


def test_unavailable_response_notices_are_deduped(build_agent):
    llm = FakeLLM(fail_on={"decision", "translate"})
    response = build_agent(llm=llm).ask_structured(normalized_request("หิมะตกไหม"))
    assert response["status"] == "unavailable"
    assert len(response["notices"]) == len(set(response["notices"]))
    json.dumps(response)
