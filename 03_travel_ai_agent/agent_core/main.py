"""Entry point of node 03: the travel AI agent orchestrator.

Order of operations for every request (fixed by the implementation plan):

    normalize history -> route -> reformulate -> translate retrieval query
    -> retrieve/rerank (node 06) -> call allowed tools (node 04)
    -> generate (node 07 prompt, provider call, node 07 parse) -> guardrails
    -> memory (own conversation only) -> audit event (node 08)

``TravelAgent.ask_structured`` is what node 02 calls. ``TravelAgent.ask``
keeps the legacy string-returning interface.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from agent_core import guardrails
from agent_core.audit import AuditEmitter, build_audit_event
from agent_core.classifier import IntentClassifier, detect_language
from agent_core.context_manager import ContextManager, memory_store
from agent_core.llm_client import GroqChatClient, LLMClientError, extract_json_object
from agent_core.planner import ExecutionPlanner, evidence_public_view
from agent_core.schemas import (
    RESPONSE_STATUS_OK,
    RESPONSE_STATUS_UNAVAILABLE,
    ContextPackage,
    OrchestrationRequest,
    OrchestrationResponse,
    RouteDecision,
    ToolResult,
)
from agent_core.settings import config_value
from agent_core.tools import ToolExecutor

logger = logging.getLogger("travel_ai_agent")

DEFAULT_DECISION_MODEL = "openai/gpt-oss-120b"
DECISION_TEMPERATURE = 0.2
DECISION_MAX_TOKENS = 1200
DECISION_ATTEMPTS = (True, False)  # json_mode per attempt
# Node 07 contract: format_prompt(original_query, history, evidence, live_data, tool_policy, language)
# returns chat messages; parse_llm_response(json_text) returns the structured decision. No network.
NODE07_INTERFACE = ("format_prompt", "parse_llm_response")

# Snapshot statuses that mean data the answer needed is missing or unreliable.
MISSING_DATA_STATUSES = ("unavailable", "stale", "partial")
SLOT_DEFAULT_NOTICES = {
    "city": "weather: no city was mentioned; checked Sapporo.",
    "line_name": "train: no line was mentioned; checked all JR Hokkaido lines.",
}


class TravelAgent:
    """Routes, gathers verified context and hands it to the decision layer."""

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        classifier: Optional[IntentClassifier] = None,
        context_manager: Optional[ContextManager] = None,
        planner: Optional[ExecutionPlanner] = None,
        generator: Optional[Any] = None,
        audit_emitter: Optional[AuditEmitter] = None,
        retriever: Optional[Any] = None,
        reranker: Optional[Any] = None,
        tool_executor: Optional[ToolExecutor] = None,
        decision_model: Optional[str] = None,
        load_models: bool = True,
    ):
        self.llm_client = llm_client if llm_client is not None else GroqChatClient()
        self.classifier = classifier if classifier is not None else IntentClassifier(llm_client=self.llm_client)
        self.context_manager = (
            context_manager
            if context_manager is not None
            else ContextManager(llm_client=self.llm_client, store=memory_store)
        )
        self.audit_emitter = audit_emitter if audit_emitter is not None else AuditEmitter()
        self.decision_model = (
            decision_model if decision_model is not None else config_value("LLM_MODEL", DEFAULT_DECISION_MODEL)
        )

        if planner is None:
            if retriever is None and load_models:
                retriever, reranker = self._build_retrieval_components(reranker)
            planner = ExecutionPlanner(
                tool_executor=tool_executor if tool_executor is not None else ToolExecutor(),
                retriever=retriever,
                reranker=reranker,
            )
        self.planner = planner

        if generator is None:
            from decision_engine.generator import Generator  # node 07: pure, no network

            generator = Generator()
        missing = [name for name in NODE07_INTERFACE if not callable(getattr(generator, name, None))]
        if missing:
            # Node 02 turns a failed start-up into HTTP 503; never answer without the decision layer.
            raise RuntimeError(f"node 07 generator is missing the expected interface: {', '.join(missing)}")
        self.generator = generator
        logger.info("travel AI agent ready (retrieval=%s)", self.planner.retriever is not None)

    @staticmethod
    def _build_retrieval_components(reranker: Optional[Any]):
        """Builds node 05/06 components. Failure degrades retrieval instead of crashing startup."""
        try:
            from data_integration.embedding_model import EmbeddingModel
            from risk_knowledge.hybrid_retriever import HybridRetriever

            retriever = HybridRetriever(EmbeddingModel())
        except Exception:
            logger.exception("retrieval components could not be initialised; running without corpus")
            return None, None

        if reranker is None and config_value("USE_RERANK", True):
            try:
                from risk_knowledge.rerankers import Reranker

                reranker = Reranker()
            except Exception:
                logger.exception("reranker could not be initialised; using hybrid order")
                reranker = None
        return retriever, reranker

    # ------------------------------------------------------------------
    # Public interface used by node 02
    # ------------------------------------------------------------------
    def ask_structured(self, normalized: Dict[str, Any]) -> Dict[str, Any]:
        request = OrchestrationRequest.from_normalized(normalized)
        return self.run(request).model_dump()

    def ask(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None, enabled_agents=None) -> str:
        """Legacy interface: returns the reply text only."""
        request = OrchestrationRequest(
            request_id=str(uuid.uuid4()),
            original_query=query,
            chat_history=chat_history or [],
            enabled_agents=enabled_agents or {},
        )
        return self.run(request).reply

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run(self, request: OrchestrationRequest) -> OrchestrationResponse:
        notices: List[str] = []
        query = request.original_query

        # 1. history (API history is authoritative)
        history, history_source = self.context_manager.resolve_history(request)
        language = detect_language(query, fallback=request.locale)

        # 2. route
        decision = self.classifier.classify_message(query, history)
        route = guardrails.validate_route(decision.route)
        needs = self.classifier.detect_context_needs(decision)
        if decision.fallback_used:
            notices.append(f"router fallback used ({decision.source}): {decision.reasoning}")
        logger.info(
            "request_id=%s route=%s confidence=%.2f fallback=%s history=%s",
            request.request_id, route, decision.confidence, decision.fallback_used, history_source,
        )

        # 3. reformulate (for retrieval only) and 4. translate retrieval query
        english_query: Optional[str] = None
        if needs["needs_retrieval"] or needs["needs_live_data"]:
            standalone, notice = self.context_manager.reformulate_query(query, history)
            if notice:
                notices.append(notice)
            english_query, notice = self.context_manager.translate_for_retrieval(standalone, language)
            if notice:
                notices.append(notice)

        # 5. plan
        slots = self.classifier.extract_slots(query, english_query)
        for slot in self.classifier.missing_required_slots(decision, slots):
            notices.append(SLOT_DEFAULT_NOTICES[slot])
        plan = self.planner.plan(decision, request, slots, retrieval_query=english_query)
        notices.extend(plan.notices)

        # 6. retrieve (node 06)
        evidence: List[Dict[str, Any]] = []
        retrieval_degraded = False
        index_version: Optional[str] = None
        if plan.needs_retrieval:
            outcome = self.planner.retrieve(plan.retrieval_query or query)
            evidence = outcome.evidence
            retrieval_degraded = outcome.degraded
            index_version = outcome.index_version
            notices.extend(outcome.notices)

        # 7. live tools (node 04)
        live_results: List[ToolResult] = self.planner.execute_tools(plan)
        for result in live_results:
            notices.extend(result.notices)
        missing_live_data = any(result.status in MISSING_DATA_STATUSES for result in live_results)

        # 8. package for node 07
        tool_policy = {
            "route": route,
            "allowed_tools": self.planner.tool_executor.allowed_tools(),
            "executed_tools": [r.call.name for r in live_results],
            "skipped_tools": plan.skipped_tools,
        }
        package = self.context_manager.build_context_package(
            request, history, evidence, [r.snapshot for r in live_results], language, tool_policy, route
        )

        # 9. generate
        try:
            decision_dict = self._generate(package)
        except LLMClientError as exc:
            logger.warning("request_id=%s decision provider unavailable: %s", request.request_id, exc)
            return self._unavailable(
                request, decision, language, evidence, live_results, notices + [f"decision provider unavailable: {exc}"]
            )

        # 10. guardrails on the decision
        try:
            result, guard_notices = guardrails.validate_decision(
                decision_dict,
                evidence_ids=[e["chunk_id"] for e in evidence],
                live_providers=[r.provider for r in live_results],
                dependency_degraded=retrieval_degraded or missing_live_data,
            )
        except guardrails.GuardrailViolation as exc:
            logger.warning("request_id=%s decision rejected: %s", request.request_id, exc)
            return self._unavailable(
                request, decision, language, evidence, live_results, notices + [f"decision rejected by guardrails: {exc}"]
            )
        notices.extend(guard_notices)
        notices.extend(result.notices)

        # A simulated source degrades the answer only when the decision actually relied on it.
        mocked_used = {r.provider for r in live_results if r.status == "mocked"} & set(result.used_live_sources)
        degraded = result.degraded or bool(mocked_used)

        # 11. memory (this conversation only)
        self.context_manager.remember(request, result.reply, history=history, history_source=history_source)

        # 12. audit (node 08)
        response = OrchestrationResponse(
            status=RESPONSE_STATUS_OK,
            reply=result.reply,
            request_id=request.request_id,
            route=route,
            degraded=degraded,
            notices=_dedupe(notices),
            evidence=[evidence_public_view(e) for e in evidence],
            live_sources=[r.public_view() for r in live_results],
            safety_level=result.safety_level,
            fallback_used=decision.fallback_used,
            language=language,
            used_evidence_ids=result.used_evidence_ids,
            used_live_sources=result.used_live_sources,
        )
        self.audit_emitter.emit(
            build_audit_event(request.request_id, route, response.degraded, evidence, live_results, index_version)
        )
        return response

    @staticmethod
    def _unavailable(
        request: OrchestrationRequest,
        decision: RouteDecision,
        language: str,
        evidence: List[Dict[str, Any]],
        live_results: List[ToolResult],
        notices: List[str],
    ) -> OrchestrationResponse:
        """Response when no trustworthy answer can be produced (node 02 maps it to HTTP 503)."""
        return OrchestrationResponse(
            status=RESPONSE_STATUS_UNAVAILABLE,
            request_id=request.request_id,
            route=decision.route,
            notices=_dedupe(notices),
            evidence=[evidence_public_view(e) for e in evidence],
            live_sources=[r.public_view() for r in live_results],
            fallback_used=decision.fallback_used,
            language=language,
        )

    # ------------------------------------------------------------------
    # Decision generation (node 07 prompt -> provider -> node 07 parse)
    # ------------------------------------------------------------------
    def _generate(self, package: ContextPackage) -> Dict[str, Any]:
        messages = self.generator.format_prompt(
            original_query=package.original_query,
            history=package.history,
            evidence=package.evidence,
            live_data=package.live_data,
            tool_policy=package.tool_policy,
            language=package.language,
        )

        last_error = "decision output could not be parsed"
        for attempt, json_mode in enumerate(DECISION_ATTEMPTS, start=1):
            raw = self.llm_client.complete(
                messages,
                model=self.decision_model,
                temperature=DECISION_TEMPERATURE,
                max_tokens=DECISION_MAX_TOKENS,
                json_mode=json_mode,
            )
            parsed = extract_json_object(raw)
            if parsed is None:
                logger.warning("decision attempt %d returned no JSON object", attempt)
                continue

            decision = self.generator.parse_llm_response(json.dumps(_coerce_decision(parsed), ensure_ascii=False))
            if _is_generator_fallback(decision):
                last_error = "; ".join(decision.get("notices") or [last_error])
                logger.warning("decision attempt %d rejected by node 07 validation", attempt)
                continue
            return decision

        raise LLMClientError(last_error)


def _coerce_decision(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes loosely typed model output (null lists, numeric ids) before node 07's strict parse.

    Guardrails still verify every id against what was actually supplied.
    """

    def string_list(value: Any) -> List[str]:
        if isinstance(value, (list, tuple)):
            return [str(v) for v in value if v is not None and str(v).strip()]
        if isinstance(value, str) and value.strip():
            return [value]
        return []

    coerced = dict(parsed)
    coerced["reply"] = parsed.get("reply") if isinstance(parsed.get("reply"), str) else ""
    coerced["safety_level"] = str(parsed.get("safety_level") or "unknown")
    coerced["used_evidence_ids"] = string_list(parsed.get("used_evidence_ids"))
    coerced["used_live_sources"] = string_list(parsed.get("used_live_sources"))
    coerced["degraded"] = bool(parsed.get("degraded", False))
    coerced["notices"] = string_list(parsed.get("notices"))
    return coerced


def _is_generator_fallback(decision: Dict[str, Any]) -> bool:
    # Node 07 marks its own fallback with this notice prefix (decision_engine/generator.py).
    notices = decision.get("notices") or []
    return any(str(n).startswith("Fallback activated") for n in notices)


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out
