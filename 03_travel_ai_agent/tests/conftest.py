"""Shared fixtures for node 03 tests.

Unit tests depend on node 03 only: the provider, node 04 adapters, node 06
retriever, node 07 generator and node 08 sink are all fakes injected through
constructors. Only ``03_travel_ai_agent`` is on ``sys.path`` (see pytest.ini).
Contract tests against the real neighbouring nodes live in test_contracts.py.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import pytest

from agent_core.llm_client import LLMClientError


DECISION_OK = {
    "reply": "Stay indoors and keep warm. Call **119** if you are injured.",
    "safety_level": "advisory",
    "used_evidence_ids": ["chunk-1"],
    "used_live_sources": ["meteosource"],
    "degraded": False,
    "notices": [],
}


class FakeLLM:
    """Answers by prompt type so one fake serves router, transforms and decision."""

    def __init__(
        self,
        route: str = "rag+realtime",
        confidence: float = 0.95,
        tools: Optional[List[str]] = None,
        decision: Optional[Dict[str, Any]] = None,
        decision_raw: Optional[List[str]] = None,
        fail_on: Optional[set] = None,
        configured: bool = True,
    ):
        self.route = route
        self.confidence = confidence
        # Default: the router names every tool; tests narrow this to exercise tool selection.
        self.tools = ["weather", "disaster", "train"] if tools is None else tools
        self.decision = decision or DECISION_OK
        self.decision_raw = list(decision_raw) if decision_raw else None
        self.fail_on = fail_on or set()
        self.is_configured = configured
        self.calls: List[Dict[str, Any]] = []

    def complete(self, messages, model, temperature=0.0, max_tokens=1000, json_mode=False):
        system = messages[0]["content"]
        kind = self._kind(system)
        self.calls.append({"kind": kind, "model": model, "json_mode": json_mode, "messages": messages})
        if kind in self.fail_on:
            raise LLMClientError(f"{kind} provider down")
        if kind == "router":
            payload = {"route": self.route, "confidence": self.confidence, "reasoning": "fake"}
            if self.tools is not None:
                payload["tools"] = self.tools
            return json.dumps(payload)
        if kind == "reformulate":
            return "standalone question"
        if kind == "translate":
            return "english retrieval query"
        if kind == "summarize":
            return "summary of earlier turns"
        if self.decision_raw is not None:
            return self.decision_raw.pop(0) if self.decision_raw else "{}"
        return json.dumps(self.decision)

    @staticmethod
    def _kind(system: str) -> str:
        if "intent classifier" in system:
            return "router"
        if "standalone question" in system:
            return "reformulate"
        if "professional translator" in system:
            return "translate"
        if "conversation summarizer" in system:
            return "summarize"
        return "decision"


class FakeGenerator:
    """Stands in for node 07. Same method names and prompt markers; no network."""

    SAFETY_LEVELS = ("unknown", "advisory", "urgent")

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def format_prompt(self, original_query, history=None, evidence=None, live_data=None, tool_policy=None, language="th"):
        self.calls.append({"original_query": original_query, "history": history, "evidence": evidence,
                           "live_data": live_data, "tool_policy": tool_policy, "language": language})
        blocks = [f"[Evidence ID: {e.get('chunk_id')}]\n{e.get('text')}" for e in evidence or []]
        blocks += [f"[Live Source: {s.get('provider')} | Status: {s.get('status')}]" for s in live_data or []]
        system = f"Decision layer. Answer in '{language}'. Return JSON.\n" + "\n\n".join(blocks)
        messages = [{"role": "system", "content": system}]
        messages += [{"role": m["role"], "content": m["content"]} for m in (history or [])[-6:]]
        messages.append({"role": "user", "content": original_query})
        return messages

    def parse_llm_response(self, json_str):
        try:
            data = json.loads(json_str)
            assert isinstance(data["reply"], str)
            assert data["safety_level"] in self.SAFETY_LEVELS
            for key in ("used_evidence_ids", "used_live_sources", "notices"):
                assert isinstance(data[key], list) and all(isinstance(v, str) for v in data[key])
            assert isinstance(data["degraded"], bool)
        except Exception as exc:
            return {"reply": "fallback", "safety_level": "unknown", "used_evidence_ids": [],
                    "used_live_sources": [], "degraded": True, "notices": [f"Fallback activated: {exc!r}"]}
        data["reply"] = re.sub(r"<[^>]+>", "", data["reply"])
        return data


class FakeRetriever:
    def __init__(self, items=None, ready=True, degraded=False, notices=None, raise_error=False):
        self.items = items if items is not None else [
            {"chunk_id": "chunk-1", "text": "Stay indoors during a blizzard.",
             "metadata": {"source_file": "blizzard.pdf", "page": 3, "source_version": "v1", "situation": "blizzard"}},
            {"chunk_id": "chunk-2", "text": "Call 119 for an ambulance.",
             "metadata": {"source_file": "contacts.json", "source_version": "v2", "situation": "emergency"}},
        ]
        self.is_ready = ready
        self.degraded = degraded
        self.notices = notices or []
        self.index_version = "index-2026-09"
        self.raise_error = raise_error
        self.calls: List[Dict[str, Any]] = []

    def retrieve(self, query, top_k=None):
        self.calls.append({"query": query, "top_k": top_k})
        if self.raise_error:
            raise RuntimeError("index broken")
        return list(self.items)


class FakeReranker:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def rerank(self, query, chunks, top_k=None):
        self.calls.append({"query": query, "n": len(chunks), "top_k": top_k})
        return list(chunks)[: top_k or len(chunks)]


def snapshot(provider: str, kind: str, scope: str, status: str = "ok", **extra) -> Dict[str, Any]:
    base = {
        "provider": provider,
        "kind": kind,
        "scope": scope,
        "status": status,
        "fetched_at": "2026-09-26T00:00:00Z",
        "expires_at": None,
        "data": {"summary": "light snow"},
        "source_url": "https://example.test",
        "error_code": None,
        "notice": None,
    }
    base.update(extra)
    return base


class FakeAdapters:
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def weather(self, city):
        self.calls.append({"tool": "weather", "arg": city})
        return snapshot("meteosource", "weather", city)

    def disaster(self, region):
        self.calls.append({"tool": "disaster", "arg": region})
        return snapshot("jma", "disaster", region)

    def train(self, line):
        self.calls.append({"tool": "train", "arg": line})
        return snapshot("jr_hokkaido_simulator", "train", line, status="mocked", notice="Simulated status.")

    def as_dict(self):
        return {"weather": self.weather, "disaster": self.disaster, "train": self.train}


@pytest.fixture
def fake_llm():
    return FakeLLM()


@pytest.fixture
def fake_retriever():
    return FakeRetriever()


@pytest.fixture
def fake_adapters():
    return FakeAdapters()


@pytest.fixture
def audit_sink():
    events: List[Dict[str, Any]] = []
    return events


@pytest.fixture
def build_agent(fake_llm, fake_retriever, fake_adapters, audit_sink):
    """Factory for a fully faked TravelAgent."""
    from agent_core.audit import AuditEmitter
    from agent_core.classifier import IntentClassifier
    from agent_core.context_manager import ContextManager, ConversationMemoryStore
    from agent_core.main import TravelAgent
    from agent_core.planner import ExecutionPlanner
    from agent_core.tools import ToolExecutor

    def factory(llm=None, retriever=None, adapters=None, store=None, use_memory=True, reranker=None):
        llm = llm if llm is not None else fake_llm
        retriever = fake_retriever if retriever is None else retriever
        adapters = adapters if adapters is not None else fake_adapters
        store = store if store is not None else ConversationMemoryStore()
        executor = ToolExecutor(adapters=adapters.as_dict())
        planner = ExecutionPlanner(
            tool_executor=executor,
            retriever=retriever if retriever is not False else None,
            reranker=reranker if reranker is not None else FakeReranker(),
            retriever_top_k=10,
            final_top_k=2,
        )
        agent = TravelAgent(
            llm_client=llm,
            classifier=IntentClassifier(llm_client=llm, model="router-model"),
            context_manager=ContextManager(llm_client=llm, store=store, model="transform-model", use_memory=use_memory),
            planner=planner,
            audit_emitter=AuditEmitter(sink=audit_sink.append),
            generator=FakeGenerator(),
            decision_model="decision-model",
            load_models=False,
        )
        agent._store = store
        return agent

    return factory


def normalized_request(query: str, request_id: str = "5a3d7c18-4b0e-4c2a-9f4d-1e6f3a2b9c01", **overrides):
    payload = {
        "request_id": request_id,
        "original_query": query,
        "chat_history": [],
        "enabled_agents": {"weather": True, "disaster": True, "train": True},
        "received_at": "2026-09-26T00:00:00+00:00",
        "input_mode": "legacy",
    }
    payload.update(overrides)
    return payload
