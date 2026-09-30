"""Behaviour that keeps node 03 self-contained: legacy import paths used by other
nodes, and honest reporting when a neighbouring node breaks its contract."""
import pytest

from agent_core import guardrails
from agent_core.main import TravelAgent
from agent_core.planner import ExecutionPlanner
from agent_core.schemas import OrchestrationRequest, RouteDecision, ToolCall
from agent_core.tools import ToolExecutor
from conftest import FakeAdapters, FakeGenerator, FakeLLM, FakeReranker, normalized_request


# --- legacy import paths kept for node 02 and node 08 --------------------------

def test_legacy_global_memory_is_reset_only_and_clears_per_conversation_store():
    from agent_core.context_manager import memory_store
    from agent_core.memory import global_memory

    memory_store.get("conv-legacy").add_turn("user", "trapped in Otaru")
    assert len(memory_store) >= 1
    global_memory.clear()
    assert len(memory_store) == 0
    # it stores nothing and cannot be used as a shared history
    for name in ("get_history", "add_user_message", "add_ai_message", "history"):
        assert not hasattr(global_memory, name)


def test_legacy_query_transformer_keeps_old_methods():
    from agent_core.query_transform import QueryTransformer

    transformer = QueryTransformer(llm_client=FakeLLM(), model="m")
    assert transformer.translate_to_english("หิมะตกไหม") == "english retrieval query"
    assert transformer.translate_to_english("Is it snowing?") == "Is it snowing?"
    assert transformer.reformulate_query("and Otaru?", [{"role": "ai", "content": "Sapporo is snowy"}]) == "standalone question"
    assert transformer.reformulate_query("and Otaru?", None) == "and Otaru?"


def test_legacy_query_transformer_returns_original_text_when_provider_is_down():
    from agent_core.query_transform import QueryTransformer

    transformer = QueryTransformer(llm_client=FakeLLM(fail_on={"translate"}), model="m")
    assert transformer.translate_to_english("หิมะตกไหม") == "หิมะตกไหม"


# --- node 04 contract ----------------------------------------------------------

def test_plain_text_from_an_adapter_is_reported_as_incompatible():
    executor = ToolExecutor(adapters={"weather": lambda city: "Current weather: -5C, snow"})
    snapshot = executor.execute(ToolCall(name="weather", args={"city": "Sapporo"}))
    assert snapshot["status"] == "unavailable"
    assert snapshot["error_code"] == "INCOMPATIBLE_ADAPTER_OUTPUT"
    assert snapshot["data"] is None


def test_node04_import_failure_is_named_in_the_notice(monkeypatch):
    import agent_core.tools as tools

    monkeypatch.setattr(tools, "ADAPTER_IMPORT_ERROR", "NameError: name 'Tuple_Quake_Result' is not defined")
    executor = tools.ToolExecutor(adapters={"train": FakeAdapters().train})
    assert executor.allowed_tools() == ["train"]
    assert "could not be imported" in executor.unavailable_reason("weather")
    assert "NameError" in executor.unavailable_reason("weather")
    assert executor.unavailable_reason("train") == "adapter is not available"

    planner = ExecutionPlanner(tool_executor=executor, retriever_top_k=5, final_top_k=2)
    plan = planner.plan(
        RouteDecision(route="realtime", tool_hints=["weather", "train"]),
        OrchestrationRequest(request_id="r", original_query="q"),
        {},
        None,
    )
    assert [c.name for c in plan.tool_calls] == ["train"]
    assert any("could not be imported" in n for n in plan.notices)


def test_local_validators_apply_node04_defaults_and_reject_unsafe_input():
    local = guardrails.LOCAL_VALIDATORS
    agents = {"weather": True, "disaster": True, "train": True}
    region = guardrails.validate_tool_args(ToolCall(name="disaster", args={"region": None}), agents, ["disaster"], local)
    line = guardrails.validate_tool_args(ToolCall(name="train", args={"line_name": " "}), agents, ["train"], local)
    assert region.args == {"region": "Hokkaido"} and line.args == {"line_name": "All"}
    with pytest.raises(guardrails.GuardrailViolation):
        guardrails.validate_tool_args(ToolCall(name="weather", args={"city": None}), agents, ["weather"], local)
    with pytest.raises(guardrails.GuardrailViolation):
        guardrails.validate_tool_args(ToolCall(name="weather", args={"city": "a/b?c"}), agents, ["weather"], local)


# --- node 06 contract ----------------------------------------------------------

class WrapperRetriever:
    """Node 06 style: retrieve_response() returns an evidence wrapper."""

    def __init__(self, degraded=False, notices=None):
        self.calls = []
        self._degraded = degraded
        self._notices = notices or []

    def retrieve_response(self, query, top_k=None):
        self.calls.append((query, top_k))

        class Wrapper:
            results = [{"chunk_id": "w-1", "text": "Evacuate to high ground.", "metadata": {"source_version": "v9"},
                        "rank": 1, "score": 0.8, "retrieval_method": "hybrid"}]
            index_version = "idx-wrapper"
            retrieved_at = "2026-09-27T00:00:00+00:00"
            degraded = self._degraded
            notices = self._notices

        return Wrapper()


def test_planner_prefers_the_node06_evidence_wrapper():
    retriever = WrapperRetriever()
    outcome = ExecutionPlanner(retriever=retriever, reranker=FakeReranker(), retriever_top_k=4, final_top_k=2).retrieve("tsunami")
    assert retriever.calls == [("tsunami", 4)]
    assert outcome.index_version == "idx-wrapper" and outcome.retrieved_at == "2026-09-27T00:00:00+00:00"
    assert outcome.evidence[0]["chunk_id"] == "w-1" and outcome.evidence[0]["retrieved_at"] == outcome.retrieved_at
    assert outcome.degraded is False


def test_degraded_wrapper_is_reported_with_its_latest_notices():
    retriever = WrapperRetriever(degraded=True, notices=["old", "index missing", "old"])
    outcome = ExecutionPlanner(retriever=retriever, retriever_top_k=4, final_top_k=2).retrieve("q")
    assert outcome.degraded is True
    assert outcome.notices == ["retrieval: index missing", "retrieval: old"]


# --- node 07 contract ----------------------------------------------------------

def test_agent_refuses_to_start_without_the_node07_interface():
    class NotAGenerator:
        def generate(self, *args, **kwargs):
            return "old interface"

    with pytest.raises(RuntimeError, match="format_prompt, parse_llm_response"):
        TravelAgent(llm_client=FakeLLM(), generator=NotAGenerator(), load_models=False)


def test_original_query_is_never_rewritten(build_agent):
    agent = build_agent()
    generator = agent.generator
    history = [{"role": "user", "content": "ขับรถไปโอตารุ"}, {"role": "assistant", "content": "หิมะตกหนัก"}]
    agent.ask_structured(normalized_request("แล้วพรุ่งนี้ล่ะ", chat_history=history, input_mode="messages"))
    assert isinstance(generator, FakeGenerator)
    assert generator.calls[-1]["original_query"] == "แล้วพรุ่งนี้ล่ะ"
    assert generator.calls[-1]["language"] == "th"
