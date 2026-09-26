from agent_core.planner import ExecutionPlanner, evidence_public_view, evidence_to_dict
from agent_core.schemas import OrchestrationRequest, RouteDecision
from agent_core.tools import ToolExecutor
from conftest import FakeAdapters, FakeReranker, FakeRetriever


def make_planner(adapters=None, retriever=None, reranker=None):
    adapters = adapters or FakeAdapters()
    return ExecutionPlanner(
        tool_executor=ToolExecutor(adapters=adapters.as_dict()),
        retriever=retriever,
        reranker=reranker,
        retriever_top_k=5,
        final_top_k=2,
    )


def request(**agents):
    return OrchestrationRequest(request_id="r", original_query="q", enabled_agents=agents)


def test_general_route_plans_nothing():
    plan = make_planner().plan(RouteDecision(route="general"), request(), {"city": None}, "q")
    assert plan.needs_retrieval is False and plan.tool_calls == []


def test_rag_route_plans_retrieval_only():
    plan = make_planner().plan(RouteDecision(route="rag"), request(), {"city": None}, "english q")
    assert plan.needs_retrieval is True and plan.retrieval_query == "english q" and plan.tool_calls == []


def test_disabled_tool_is_skipped_and_never_called():
    adapters = FakeAdapters()
    planner = make_planner(adapters)
    plan = planner.plan(RouteDecision(route="realtime"), request(train=False), {"city": "Sapporo"}, None)
    assert plan.skipped_tools["train"] == "disabled_by_caller"
    assert [c.name for c in plan.tool_calls] == ["weather", "disaster"]
    planner.execute_tools(plan)
    assert {c["tool"] for c in adapters.calls} == {"weather", "disaster"}


def test_tool_hints_limit_calls_and_missing_city_uses_default():
    plan = make_planner().plan(
        RouteDecision(route="rag+realtime", tool_hints=["weather"]), request(), {"city": None}, "q"
    )
    assert [c.name for c in plan.tool_calls] == ["weather"]
    assert plan.tool_calls[0].args == {"city": "Sapporo"}
    assert plan.skipped_tools["train"] == "not_needed_for_query"
    assert plan.notices == []


def test_unknown_hints_query_every_permitted_tool_with_notice():
    plan = make_planner().plan(RouteDecision(route="realtime", tool_hints=None), request(), {}, None)
    assert [c.name for c in plan.tool_calls] == ["weather", "disaster", "train"]
    assert any("all permitted live sources" in n for n in plan.notices)


def test_explicit_empty_hints_from_schema_are_kept_as_none():
    # An empty list is not "no tools": the classifier converts it to None (unknown).
    assert RouteDecision(route="realtime", tool_hints=None).tool_hints is None
    assert RouteDecision(route="realtime", tool_hints=["bogus"]).tool_hints == []


def test_unavailable_adapter_is_skipped():
    adapters = FakeAdapters().as_dict()
    adapters["weather"] = None
    planner = ExecutionPlanner(tool_executor=ToolExecutor(adapters=adapters), retriever=None, retriever_top_k=5, final_top_k=2)
    plan = planner.plan(RouteDecision(route="realtime", tool_hints=["weather", "disaster"]), request(), {}, None)
    assert plan.skipped_tools["weather"] == "adapter_unavailable"
    assert [c.name for c in plan.tool_calls] == ["disaster"]


def test_execute_tools_wraps_adapter_exception_as_unavailable():
    adapters = FakeAdapters().as_dict()

    def boom(_):
        raise RuntimeError("provider exploded")

    adapters["disaster"] = boom
    planner = ExecutionPlanner(tool_executor=ToolExecutor(adapters=adapters), retriever_top_k=5, final_top_k=2)
    plan = planner.plan(RouteDecision(route="realtime", tool_hints=["disaster", "train"]), request(), {}, None)
    results = planner.execute_tools(plan)
    by_tool = {r.call.name: r for r in results}
    assert by_tool["disaster"].status == "unavailable"
    assert by_tool["disaster"].snapshot["error_code"] == "ADAPTER_ERROR"
    assert by_tool["train"].status == "mocked" and by_tool["train"].notices


def test_retrieve_uses_reranker_and_flattens_evidence():
    retriever, reranker = FakeRetriever(), FakeReranker()
    outcome = make_planner(retriever=retriever, reranker=reranker).retrieve("english q")
    assert retriever.calls == [{"query": "english q", "top_k": 5}]
    assert reranker.calls[0]["top_k"] == 2
    assert [e["chunk_id"] for e in outcome.evidence] == ["chunk-1", "chunk-2"]
    assert outcome.index_version == "index-2026-09" and outcome.degraded is False


def test_retrieve_without_retriever_or_broken_index_is_degraded():
    outcome = make_planner(retriever=None).retrieve("q")
    assert outcome.degraded and outcome.evidence == [] and outcome.notices
    outcome = make_planner(retriever=FakeRetriever(raise_error=True)).retrieve("q")
    assert outcome.degraded and "retrieval failed" in outcome.notices[0]
    outcome = make_planner(retriever=FakeRetriever(items=[], ready=False, notices=["index missing"])).retrieve("q")
    assert outcome.degraded and outcome.notices == ["retrieval: index missing"]


def test_retriever_notices_are_capped_and_deduped():
    noisy = FakeRetriever(items=[], ready=False, notices=["a", "b", "a", "c", "d", "d"])
    outcome = make_planner(retriever=noisy).retrieve("q")
    assert outcome.notices == ["retrieval: c", "retrieval: d", "retrieval: a"] or outcome.notices == [
        "retrieval: a", "retrieval: c", "retrieval: d"
    ]
    assert len(outcome.notices) == 3


def test_retrieve_reranker_failure_falls_back_to_hybrid_order():
    class BrokenReranker:
        def rerank(self, *a, **k):
            raise RuntimeError("model missing")

    outcome = make_planner(retriever=FakeRetriever(), reranker=BrokenReranker()).retrieve("q")
    assert len(outcome.evidence) == 2 and any("reranking unavailable" in n for n in outcome.notices)


def test_evidence_to_dict_supports_node06_objects():
    class Item:
        def to_dict(self):
            return {"chunk": {"chunk_id": "c9", "text": "t", "metadata": {"page": 2}}, "rank": 1, "score": 0.5,
                    "retrieval_method": "hybrid+rerank"}

    flat = evidence_to_dict(Item())
    assert flat["chunk_id"] == "c9" and flat["metadata"]["page"] == 2 and flat["score"] == 0.5
    view = evidence_public_view({"chunk_id": "c9", "text": "x" * 500, "metadata": {"source_file": "f.pdf", "page": 2}})
    assert view["source_file"] == "f.pdf" and len(view["excerpt"]) == 300
