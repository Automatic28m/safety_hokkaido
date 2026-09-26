"""Execution logic for node 03.

The planner turns a ``RouteDecision`` into an ``ExecutionPlan`` (which node 06
retrieval and node 04 tools are permitted) and then executes it. Every tool
call passes ``guardrails.validate_tool_args`` before and
``guardrails.validate_tool_result`` after execution.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent_core import guardrails
from agent_core.classifier import DEFAULT_CITY, DEFAULT_LINE, DEFAULT_REGION
from agent_core.schemas import TOOL_NAMES, ExecutionPlan, OrchestrationRequest, RouteDecision, ToolCall, ToolResult
from agent_core.settings import config_value
from agent_core.tools import ToolExecutor

logger = logging.getLogger("travel_ai_agent")

DEFAULT_RETRIEVER_TOP_K = 10
DEFAULT_FINAL_TOP_K = 3
EXCERPT_CHARS = 300
MAX_RETRIEVER_NOTICES = 3

# Default scope per tool when the user named none. Conservative Hokkaido-wide values.
DEFAULT_TOOL_ARGS: Dict[str, Dict[str, str]] = {
    "weather": {"city": DEFAULT_CITY},
    "disaster": {"region": DEFAULT_REGION},
    "train": {"line_name": DEFAULT_LINE},
}
SLOT_FOR_TOOL: Dict[str, str] = {"weather": "city", "disaster": "region", "train": "line_name"}


class RetrievalOutcome:
    def __init__(self) -> None:
        self.evidence: List[Dict[str, Any]] = []
        self.notices: List[str] = []
        self.degraded: bool = False
        self.index_version: Optional[str] = None
        self.retrieved_at: Optional[str] = None


def _latest_unique(notices: Any, limit: int = MAX_RETRIEVER_NOTICES) -> List[str]:
    """Node 06 accumulates notices for the process lifetime; keep only the latest few, in order."""
    seen: List[str] = []
    for notice in reversed(list(notices or [])):
        text = str(notice)
        if text and text not in seen:
            seen.append(text)
        if len(seen) >= limit:
            break
    return list(reversed(seen))


def evidence_to_dict(item: Any) -> Optional[Dict[str, Any]]:
    """Flattens a node 06 ``RetrievalResultItem`` (or legacy dict) into a plain dict."""
    if item is None:
        return None
    if hasattr(item, "to_dict"):
        try:
            raw = item.to_dict()
        except Exception:  # pragma: no cover - defensive
            return None
        chunk = raw.get("chunk") if isinstance(raw, dict) else None
        if isinstance(chunk, dict):
            return {
                "chunk_id": str(chunk.get("chunk_id", "")),
                "text": str(chunk.get("text", "")),
                "metadata": dict(chunk.get("metadata") or {}),
                "rank": raw.get("rank"),
                "score": raw.get("score"),
                "retrieval_method": raw.get("retrieval_method"),
            }
        if isinstance(raw, dict) and "text" in raw:
            item = raw
    if isinstance(item, dict):
        metadata = item.get("metadata") or {}
        if hasattr(metadata, "model_dump"):
            metadata = metadata.model_dump()
        return {
            "chunk_id": str(item.get("chunk_id", "")),
            "text": str(item.get("text", "")),
            "metadata": dict(metadata) if isinstance(metadata, dict) else {},
            "rank": item.get("rank"),
            "score": item.get("score"),
            "retrieval_method": item.get("retrieval_method"),
        }
    return None


def evidence_public_view(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Citation view returned to node 02 (full chunk text is not echoed)."""
    metadata = evidence.get("metadata") or {}
    return {
        "chunk_id": evidence.get("chunk_id"),
        "rank": evidence.get("rank"),
        "score": evidence.get("score"),
        "retrieval_method": evidence.get("retrieval_method"),
        "source_file": metadata.get("source_file"),
        "page": metadata.get("page"),
        "url": metadata.get("url"),
        "situation": metadata.get("situation"),
        "source_version": metadata.get("source_version"),
        "retrieved_at": evidence.get("retrieved_at"),
        "excerpt": (evidence.get("text") or "")[:EXCERPT_CHARS],
    }


class ExecutionPlanner:
    def __init__(
        self,
        tool_executor: Optional[ToolExecutor] = None,
        retriever: Optional[Any] = None,
        reranker: Optional[Any] = None,
        retriever_top_k: Optional[int] = None,
        final_top_k: Optional[int] = None,
    ):
        self.tool_executor = tool_executor if tool_executor is not None else ToolExecutor()
        self.retriever = retriever
        self.reranker = reranker
        self.retriever_top_k = int(retriever_top_k or config_value("RETRIEVER_TOP_K", DEFAULT_RETRIEVER_TOP_K))
        self.final_top_k = int(final_top_k or config_value("FINAL_TOP_K", DEFAULT_FINAL_TOP_K))

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------
    def plan(
        self,
        decision: RouteDecision,
        request: OrchestrationRequest,
        slots: Dict[str, Optional[str]],
        retrieval_query: Optional[str],
    ) -> ExecutionPlan:
        plan = ExecutionPlan(route=decision.route, needs_retrieval=decision.needs_retrieval)
        if plan.needs_retrieval:
            plan.retrieval_query = retrieval_query

        if not decision.needs_live_data:
            return plan

        allowed = set(self.tool_executor.allowed_tools())
        if decision.tool_hints is None:
            wanted = list(TOOL_NAMES)
            plan.notices.append("no specific live source was identified; all permitted live sources were queried.")
        else:
            wanted = decision.tool_hints

        for name in TOOL_NAMES:
            if name not in wanted:
                plan.skipped_tools[name] = "not_needed_for_query"
                continue
            if request.enabled_agents.get(name, True) is False:
                plan.skipped_tools[name] = "disabled_by_caller"
                continue
            if name not in allowed:
                plan.skipped_tools[name] = "adapter_unavailable"
                plan.notices.append(f"{name}: live data unavailable; {self.tool_executor.unavailable_reason(name)}.")
                continue

            call = self._build_call(name, slots)
            try:
                validated = guardrails.validate_tool_args(call, request.enabled_agents, allowed)
            except guardrails.GuardrailViolation as exc:
                logger.warning("tool '%s' blocked by guardrail: %s", name, exc)
                plan.skipped_tools[name] = f"guardrail:{exc}"
                plan.notices.append(f"{name}: skipped ({exc}).")
                continue
            plan.tool_calls.append(validated)

        return plan

    @staticmethod
    def _build_call(name: str, slots: Dict[str, Optional[str]]) -> ToolCall:
        slot = SLOT_FOR_TOOL[name]
        value = slots.get(slot) or DEFAULT_TOOL_ARGS[name][slot]
        return ToolCall(name=name, args={slot: value})

    # ------------------------------------------------------------------
    # Retrieval (node 06)
    # ------------------------------------------------------------------
    def retrieve(self, query: str) -> RetrievalOutcome:
        outcome = RetrievalOutcome()
        if self.retriever is None:
            outcome.degraded = True
            outcome.notices.append("safety document retrieval is not available; answer is not grounded in the corpus.")
            return outcome

        try:
            if hasattr(self.retriever, "retrieve_response"):
                # Preferred node 06 contract: evidence wrapper with results, index_version,
                # retrieved_at, degraded and notices.
                wrapper = self.retriever.retrieve_response(query, top_k=self.retriever_top_k)
                candidates = list(getattr(wrapper, "results", None) or [])
                outcome.index_version = getattr(wrapper, "index_version", None) or None
                outcome.retrieved_at = getattr(wrapper, "retrieved_at", None)
                source_degraded = bool(getattr(wrapper, "degraded", False))
                source_notices = getattr(wrapper, "notices", None)
            else:
                # Compatibility reader for a node 06 that still returns a plain list.
                candidates = list(self.retriever.retrieve(query, top_k=self.retriever_top_k) or [])
                outcome.index_version = getattr(self.retriever, "index_version", None) or None
                source_degraded = getattr(self.retriever, "is_ready", True) is False or bool(
                    getattr(self.retriever, "degraded", False)
                )
                source_notices = getattr(self.retriever, "notices", None)
        except Exception as exc:
            logger.exception("retrieval failed")
            outcome.degraded = True
            outcome.notices.append(f"retrieval failed ({exc.__class__.__name__}).")
            return outcome

        if source_degraded:
            outcome.degraded = True
            latest = _latest_unique(source_notices)
            outcome.notices.extend(f"retrieval: {text}" for text in latest)
            if not latest:
                outcome.notices.append("retrieval index is not ready; answer is not grounded in the corpus.")

        if self.reranker is not None and candidates:
            try:
                selected = self.reranker.rerank(query, candidates, top_k=self.final_top_k) or []
            except Exception as exc:
                logger.warning("rerank failed (%s); using hybrid order", exc.__class__.__name__)
                outcome.notices.append("reranking unavailable; used hybrid ranking order.")
                selected = candidates[: self.final_top_k]
        else:
            selected = candidates[: self.final_top_k]

        for item in selected:
            as_dict = evidence_to_dict(item)
            if as_dict and as_dict["chunk_id"] and as_dict["text"]:
                as_dict["retrieved_at"] = outcome.retrieved_at
                outcome.evidence.append(as_dict)

        if not outcome.evidence and not outcome.degraded:
            outcome.notices.append("no matching safety document was found for this question.")
        return outcome

    # ------------------------------------------------------------------
    # Tool execution (node 04)
    # ------------------------------------------------------------------
    def execute_tools(self, plan: ExecutionPlan) -> List[ToolResult]:
        results: List[ToolResult] = []
        for call in plan.tool_calls:
            snapshot = self.tool_executor.execute(call)
            validated, notices = guardrails.validate_tool_result(call.name, snapshot)
            results.append(ToolResult(call=call, snapshot=validated, notices=notices))
        return results
