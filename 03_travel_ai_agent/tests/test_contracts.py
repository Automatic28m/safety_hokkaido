"""Contract tests against the real neighbouring nodes (02, 04, 06, 07, 08).

Node 03 never edits those nodes. When one of them is missing or fails to import,
the matching test is skipped with the reason and the owning node, so the gap is
visible as "pending" instead of breaking node 03's own suite.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from agent_core import guardrails
from agent_core.audit import build_audit_event
from agent_core.planner import evidence_public_view, evidence_to_dict
from agent_core.schemas import ToolCall, ToolResult
from agent_core.tools import snapshot_to_dict

REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_DIRS = {
    "02": REPO_ROOT / "02_api_backend",
    "04": REPO_ROOT / "04_external_data_services",
    "06": REPO_ROOT / "06_risk_knowledge_services",
    "07": REPO_ROOT / "07_decision_llm_engine",
    "08": REPO_ROOT / "08_recommendation_feedback",
}


@pytest.fixture
def node():
    """Imports ``module`` from node ``owner`` with that node's folder on sys.path; skips on failure."""
    added = []

    def load(owner: str, module: str):
        folder = NODE_DIRS[owner]
        if not folder.is_dir():
            pytest.skip(f"node {owner} is not present in this checkout (owner: node {owner})")
        for path in (str(folder), str(NODE_DIRS["02"])):
            if path not in sys.path:
                sys.path.append(path)
                added.append(path)
        try:
            return importlib.import_module(module)
        except Exception as exc:  # contract not available yet
            pytest.skip(f"node {owner} `{module}` cannot be imported: {exc.__class__.__name__}: {exc} (owner: node {owner})")

    yield load
    for path in added:
        if path in sys.path:
            sys.path.remove(path)


def test_node04_snapshot_contract(node):
    models = node("04", "external_data.models")
    snapshot = models.LiveDataSnapshot(
        provider="jma", kind="disaster", scope="Hokkaido", status="stale",
        fetched_at="2026-09-27T00:00:00Z", data={"earthquakes": {}}, source_url="https://www.jma.go.jp/bosai/",
    )
    as_dict = snapshot_to_dict(snapshot)
    checked, notices = guardrails.validate_tool_result("disaster", as_dict)
    assert checked["status"] == "stale" and checked["provider"] == "jma"
    assert notices and "older than its freshness window" in notices[0]
    json.dumps(checked)


def test_node04_train_adapter_is_reported_as_mocked(node):
    tools = node("04", "external_data.tools")
    from agent_core.tools import ToolExecutor

    executor = ToolExecutor(adapters={"train": tools.check_train_status})
    snapshot = executor.execute(ToolCall(name="train", args={"line_name": "Rapid Airport"}))
    checked, notices = guardrails.validate_tool_result("train", snapshot)
    assert checked["status"] == "mocked" and "simulated" in notices[0]


def test_node06_evidence_contract(node):
    models = node("06", "risk_knowledge.models")
    item = models.RetrievalResultItem(
        chunk=models.EvidenceChunk(
            chunk_id="c1", text="Stay indoors.",
            metadata=models.EvidenceChunkMetadata(source_file="a.pdf", page=3, source_version="v1"),
        ),
        rank=1, score=0.9, retrieval_method="hybrid+rerank",
    )
    flat = evidence_to_dict(item)
    assert flat["chunk_id"] == "c1" and flat["metadata"]["page"] == 3 and flat["score"] == 0.9
    view = evidence_public_view(flat)
    assert view["source_file"] == "a.pdf" and view["retrieval_method"] == "hybrid+rerank"

    wrapper = models.RiskKnowledgeResponse(results=[item], index_version="idx", degraded=False)
    assert wrapper.results[0].chunk.chunk_id == "c1" and wrapper.retrieved_at


def test_node07_prompt_and_parse_contract(node):
    generator_module = node("07", "decision_engine.generator")
    generator = generator_module.Generator()
    evidence = [{"chunk_id": "c1", "text": "Stay indoors.", "metadata": {}}]
    live = [{"provider": "jma", "status": "ok", "data": {"quake": None}}]
    messages = generator.format_prompt(
        original_query="แผ่นดินไหวต้องทำอย่างไร", history=[], evidence=evidence, live_data=live,
        tool_policy={"route": "rag+realtime"}, language="th",
    )
    system = messages[0]["content"]
    assert "[Evidence ID: c1]" in system and "jma" in system and "'th'" in system
    assert messages[-1] == {"role": "user", "content": "แผ่นดินไหวต้องทำอย่างไร"}

    decision = generator.parse_llm_response(json.dumps({
        "reply": "อยู่ในอาคาร", "safety_level": "advisory", "used_evidence_ids": ["c1"],
        "used_live_sources": ["jma"], "degraded": False, "notices": [],
    }, ensure_ascii=False))
    result, _ = guardrails.validate_decision(decision, ["c1"], ["jma"], dependency_degraded=False)
    assert result.used_evidence_ids == ["c1"] and result.safety_level == "advisory"


def test_node08_audit_contract(node):
    service = node("08", "service")
    event = build_audit_event(
        "9a937e0e-8de4-48b1-881e-5cc0d2181418", "rag+realtime", True,
        [{"chunk_id": "c1", "metadata": {"source_version": "v1"}}],
        [ToolResult(call=ToolCall(name="train", args={"line_name": "All"}),
                    snapshot={"provider": "jr_hokkaido_simulator", "status": "mocked", "fetched_at": "2026-09-27T00:00:00Z"})],
        "",
    )
    stored = service.validate_audit(event.to_payload())
    assert stored["evidence_ids"] == ["c1"] and stored["route"] == "rag+realtime"


def test_node02_http_contract(node, build_agent):
    app_module = node("02", "api.app")
    from fastapi.testclient import TestClient

    client = TestClient(app_module.create_app(get_pipeline=lambda: build_agent()))
    ok = client.post("/ask", json={"messages": [{"role": "user", "content": "Is it safe to drive to Otaru right now?"}]})
    body = ok.json()
    assert ok.status_code == 200 and body["status"] == "ok" and body["route"] == "rag+realtime"
    assert isinstance(body["evidence"], list) and isinstance(body["live_sources"], list)

    from conftest import FakeLLM

    down = TestClient(app_module.create_app(get_pipeline=lambda: build_agent(llm=FakeLLM(fail_on={"decision"}))))
    unavailable = down.post("/ask", json={"message": "blizzard help"})
    assert unavailable.status_code == 503 and unavailable.json()["notices"]
