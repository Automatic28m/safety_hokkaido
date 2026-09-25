"""End-to-end orchestration with fakes for the provider, node 04, node 06 and node 08.

Node 07's real Generator is used so the prompt/parse contract is exercised.
"""
import json

from agent_core.context_manager import ConversationMemoryStore
from conftest import DECISION_OK, FakeLLM, FakeRetriever, normalized_request


def test_rag_realtime_flow_returns_full_contract(build_agent, fake_adapters, audit_sink):
    agent = build_agent()
    response = agent.ask_structured(normalized_request("Is it safe to drive to Otaru right now?"))

    assert response["status"] == "ok"
    assert response["reply"].startswith("Stay indoors")
    assert response["route"] == "rag+realtime"
    assert response["safety_level"] == "advisory"
    assert response["degraded"] is True  # the train source is mocked
    assert response["fallback_used"] is False and response["language"] == "en"
    assert [e["chunk_id"] for e in response["evidence"]] == ["chunk-1", "chunk-2"]
    assert all("text" not in e for e in response["evidence"])
    assert {s["tool"] for s in response["live_sources"]} == {"weather", "disaster", "train"}
    assert all("data" not in s for s in response["live_sources"])
    assert response["used_evidence_ids"] == ["chunk-1"] and response["used_live_sources"] == ["meteosource"]
    assert any("simulated" in n for n in response["notices"])

    weather_call = next(c for c in fake_adapters.calls if c["tool"] == "weather")
    assert weather_call["arg"] == "Otaru"

    assert len(audit_sink) == 1
    event = audit_sink[0]
    assert event["request_id"] == response["request_id"] and event["route"] == "rag+realtime"
    assert event["evidence_ids"] == ["chunk-1", "chunk-2"] and event["index_version"] == "index-2026-09"
    assert "Otaru" not in json.dumps(event)


def test_node07_receives_original_query_evidence_live_data_and_language(build_agent, fake_llm):
    agent = build_agent()
    agent.ask_structured(normalized_request("ตอนนี้ขับรถไปโอตารุปลอดภัยไหม"))
    decision_call = next(c for c in fake_llm.calls if c["kind"] == "decision")
    system = decision_call["messages"][0]["content"]
    assert "'th'" in system
    assert "[Evidence ID: chunk-1]" in system and "[Live Source: meteosource" in system
    assert decision_call["messages"][-1] == {"role": "user", "content": "ตอนนี้ขับรถไปโอตารุปลอดภัยไหม"}
    kinds = [c["kind"] for c in fake_llm.calls]
    assert "translate" in kinds and "reformulate" not in kinds  # no history -> no reformulation


def test_general_route_skips_retrieval_tools_and_transforms(build_agent, fake_retriever, fake_adapters, fake_llm):
    fake_llm.route, fake_llm.tools = "general", []
    response = build_agent().ask_structured(normalized_request("What is Hokkaido famous for?"))
    assert response["route"] == "general"
    assert fake_retriever.calls == [] and fake_adapters.calls == []
    assert response["evidence"] == [] and response["live_sources"] == []
    assert [c["kind"] for c in fake_llm.calls] == ["router", "decision"]


def test_caller_disabled_tool_is_never_called(build_agent, fake_adapters):
    agent = build_agent()
    agent.ask_structured(
        normalized_request("Is it safe to drive right now?", enabled_agents={"weather": False, "disaster": True, "train": True})
    )
    assert "weather" not in {c["tool"] for c in fake_adapters.calls}


def test_router_fallback_is_flagged_and_logged_in_response(build_agent, audit_sink):
    agent = build_agent(llm=FakeLLM(fail_on={"router"}))
    response = agent.ask_structured(normalized_request("What do I do during a blizzard?"))
    assert response["route"] == "rag" and response["fallback_used"] is True
    assert any(n.startswith("router fallback used (keyword)") for n in response["notices"])
    assert audit_sink[0]["route"] == "rag"


def test_decision_provider_down_returns_unavailable_without_fake_reply(build_agent, audit_sink):
    agent = build_agent(llm=FakeLLM(fail_on={"decision"}))
    response = agent.ask_structured(normalized_request("Is it safe to drive to Otaru right now?"))
    assert response["status"] == "unavailable" and response["reply"] == ""
    assert response["degraded"] is True and response["route"] == "rag+realtime"
    assert any("decision provider unavailable" in n for n in response["notices"])
    assert response["live_sources"]  # provenance is still reported
    assert audit_sink == []


def test_unparseable_decision_is_retried_then_unavailable(build_agent):
    llm = FakeLLM(decision_raw=["not json at all", "{\"reply\": \"x\", \"safety_level\": \"advisory\"}"])
    response = build_agent(llm=llm).ask_structured(normalized_request("blizzard help"))
    assert response["status"] == "unavailable"
    assert sum(1 for c in llm.calls if c["kind"] == "decision") == 2


def test_decision_referencing_unknown_evidence_is_cleaned(build_agent):
    decision = dict(DECISION_OK, used_evidence_ids=["ghost"], used_live_sources=["ghost"])
    response = build_agent(llm=FakeLLM(decision=decision)).ask_structured(normalized_request("blizzard help"))
    assert response["status"] == "ok"
    assert response["used_evidence_ids"] == [] and response["used_live_sources"] == []
    assert any("not supplied" in n for n in response["notices"])


def test_retrieval_outage_is_reported_not_hidden(build_agent):
    response = build_agent(retriever=FakeRetriever(items=[], ready=False, notices=["vector index missing"])).ask_structured(
        normalized_request("What do I do during a blizzard?")
    )
    assert response["status"] == "ok" and response["degraded"] is True
    assert "retrieval: vector index missing" in response["notices"]


def test_memory_is_isolated_per_conversation_and_api_history_wins(build_agent, fake_llm):
    store = ConversationMemoryStore()
    agent = build_agent(store=store)
    agent.ask_structured(normalized_request("blizzard in Otaru", conversation_id="conv-a"))
    agent.ask_structured(normalized_request("earthquake in Sapporo", conversation_id="conv-b"))

    assert [t["content"] for t in store.get("conv-a").get_history()][0] == "blizzard in Otaru"
    assert [t["content"] for t in store.get("conv-b").get_history()][0] == "earthquake in Sapporo"

    # follow-up in conv-a uses conv-a memory only -> reformulation sees "Otaru", never "Sapporo"
    fake_llm.calls.clear()
    agent.ask_structured(normalized_request("and tomorrow?", conversation_id="conv-a"))
    reformulate = next(c for c in fake_llm.calls if c["kind"] == "reformulate")
    prompt = reformulate["messages"][-1]["content"]
    assert "Otaru" in prompt and "Sapporo" not in prompt

    # API history is authoritative even when memory exists for the conversation
    fake_llm.calls.clear()
    agent.ask_structured(
        normalized_request(
            "and tonight?",
            conversation_id="conv-a",
            chat_history=[{"role": "user", "content": "client says Hakodate"}, {"role": "user", "content": "and tonight?"}],
            input_mode="messages",
        )
    )
    reformulate = next(c for c in fake_llm.calls if c["kind"] == "reformulate")
    prompt = reformulate["messages"][-1]["content"]
    assert "Hakodate" in prompt and "Otaru" not in prompt


def test_anonymous_requests_leave_no_server_memory(build_agent):
    store = ConversationMemoryStore()
    build_agent(store=store).ask_structured(normalized_request("blizzard help"))
    assert len(store) == 0


def test_legacy_ask_returns_reply_string(build_agent):
    reply = build_agent().ask("What do I do during a blizzard?", chat_history=None, enabled_agents={"train": False})
    assert isinstance(reply, str) and reply.startswith("Stay indoors")


def test_response_is_json_serializable_for_node02(build_agent):
    response = build_agent().ask_structured(normalized_request("Is it safe to drive to Otaru right now?"))
    json.dumps(response)
    for key in ("reply", "request_id", "status", "route", "degraded", "notices", "evidence", "live_sources"):
        assert key in response
