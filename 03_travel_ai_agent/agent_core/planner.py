"""Execution logic for node 03.

The planner turns a ``RouteDecision`` into an ``ExecutionPlan`` (which node 06
retrieval and node 04 tools are permitted) and then executes it. Every tool
call passes ``guardrails.validate_tool_args`` before and
``guardrails.validate_tool_result`` after execution.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from agent_core import guardrails
from agent_core.classifier import DEFAULT_CITY, DEFAULT_LINE, DEFAULT_REGION
from agent_core.schemas import TOOL_NAMES, ExecutionPlan, OrchestrationRequest, RouteDecision, ToolCall, ToolResult
from agent_core.tools import ToolExecutor

logger = logging.getLogger("travel_ai_agent")

DEFAULT_RETRIEVER_TOP_K = 10
DEFAULT_FINAL_TOP_K = 3
EXCERPT_CHARS = 300


class RetrievalOutcome:
    def __init__(self) -> None:
        self.evidence: List[Dict[str, Any]] = []
        self.notices: List[str] = []
        self.degraded: bool = False
        self.index_version: Optional[str] = None


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
        if retriever_top_k is None or final_top_k is None:
            try:
                from config import config

                retriever_top_k = retriever_top_k or getattr(config, "RETRIEVER_TOP_K", DEFAULT_RETRIEVER_TOP_K)
                final_top_k = final_top_k or getattr(config, "FINAL_TOP_K", DEFAULT_FINAL_TOP_K)
            except ImportError:
                retriever_top_k = retriever_top_k or DEFAULT_RETRIEVER_TOP_K
                final_top_k = final_top_k or DEFAULT_FINAL_TOP_K
        self.retriever_top_k = int(retriever_top_k)
        self.final_top_k = int(final_top_k)

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
        wanted = decision.tool_hints or list(TOOL_NAMES)

        for name in TOOL_NAMES:
            if name not in wanted:
                plan.skipped_tools[name] = "not_needed_for_query"
                continue
            if request.enabled_agents.get(name, True) is False:
                plan.skipped_tools[name] = "disabled_by_caller"
                continue
            if name not in allowed:
                plan.skipped_tools[name] = "adapter_unavailable"
                plan.notices.append(f"{name}: adapter is not available in this deployment.")
                continue

            call, notice = self._build_call(name, slots)
            if notice:
                plan.notices.append(notice)
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
    def _build_call(name: str, slots: Dict[str, Optional[str]]) -> Tuple[ToolCall, Optional[str]]:
        if name == "weather":
            city = slots.get("city")
            if city:
                return ToolCall(name=name, args={"city": city}), None
            return (
                ToolCall(name=name, args={"city": DEFAULT_CITY}),
                f"weather: no city was mentioned; checked {DEFAULT_CITY}.",
            )
        if name == "disaster":
            return ToolCall(name=name, args={"region": slots.get("region") or DEFAULT_REGION}), None
        line = slots.get("line_name")
        if line:
            return ToolCall(name=name, args={"line_name": line}), None
        return ToolCall(name=name, args={"line_name": DEFAULT_LINE}), None

    # ------------------------------------------------------------------
    # Retrieval (node 06)
    # ------------------------------------------------------------------
    def retrieve(self, query: str) -> RetrievalOutcome:
        outcome = RetrievalOutcome()
        if self.retriever is None:
            outcome.degraded = True
            outcome.notices.append("safety document retrieval is not available; answer is not grounded in the corpus.")
            return outcome

        outcome.index_version = getattr(self.retriever, "index_version", None) or None
        if getattr(self.retriever, "is_ready", True) is False or getattr(self.retriever, "degraded", False):
            outcome.degraded = True
            for notice in getattr(self.retriever, "notices", []) or []:
                outcome.notices.append(f"retrieval: {notice}")
            if not outcome.notices:
                outcome.notices.append("retrieval index is not ready; answer is not grounded in the corpus.")

        try:
            candidates = self.retriever.retrieve(query, top_k=self.retriever_top_k) or []
        except Exception as exc:
            logger.exception("retrieval failed")
            outcome.degraded = True
            outcome.notices.append(f"retrieval failed ({exc.__class__.__name__}).")
            return outcome

        selected = candidates
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
