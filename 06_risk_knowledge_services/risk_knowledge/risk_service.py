from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone
import logging

from risk_knowledge.models import (
    RiskLevel,
    EvidenceChunk,
    RetrievalResultItem,
    RetrievalRequest,
    RiskAssessment,
    RouteInfo,
    RiskKnowledgeResponse,
)
from risk_knowledge.hybrid_retriever import HybridRetriever
from risk_knowledge.rerankers import Reranker
from risk_knowledge.risk_model import LocalRiskModel

import hashlib
import time

logger = logging.getLogger(__name__)


class RiskKnowledgeService:
    """
    Unified Facade Service for Module 06 (Risk Knowledge Services).
    
    Coordinates two-stage hybrid retrieval (Dense FAISS + Sparse BM25 + Cross-Encoder)
    with the Local Risk Model Engine to provide comprehensive safety evidence,
    risk evaluations, and route accessibility in a single canonical response.
    Includes in-memory TTL caching and emergency-adaptive category prioritization.
    """

    EMERGENCY_KEYWORDS = {
        "emergency", "urgent", "stuck", "trapped", "whiteout", "accident",
        "hypothermia", "frostbite", "blizzard", "sos", "danger", "hazard", "119", "110"
    }
    EMERGENCY_CATEGORIES = {
        "emergency", "whiteout", "blizzard", "safety", "survival", "firstaid", "evacuation", "disaster"
    }

    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        reranker: Optional[Reranker] = None,
        risk_model: Optional[LocalRiskModel] = None,
        enable_reranker: bool = True,
        cache_ttl_seconds: int = 90,
    ):
        self.retriever = retriever
        self.reranker = reranker if enable_reranker else None
        self.risk_model = risk_model or LocalRiskModel()
        self.enable_reranker = enable_reranker
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Tuple[RiskKnowledgeResponse, float]] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def _make_cache_key(
        self,
        query: str,
        top_k: int,
        weather_snapshot: Any,
        disaster_snapshot: Any,
        transit_snapshot: Any,
        route_context: Optional[Dict[str, Any]],
        evaluate_risk: bool,
    ) -> str:
        def _repr_snap(s: Any) -> str:
            if s is None:
                return "none"
            if hasattr(s, "to_dict"):
                return str(s.to_dict().get("data", {}))
            if isinstance(s, dict):
                return str(s.get("data", s))
            return str(s)

        raw = (
            f"q:{query.strip().lower()}|k:{top_k}|ev:{evaluate_risk}|"
            f"w:{_repr_snap(weather_snapshot)}|d:{_repr_snap(disaster_snapshot)}|"
            f"t:{_repr_snap(transit_snapshot)}|ctx:{str(route_context or {})}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_cache_stats(self) -> Dict[str, int]:
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "cache_size": len(self._cache),
        }

    def clear_cache(self) -> None:
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def _ensure_retriever(self) -> Optional[HybridRetriever]:
        if self.retriever is None:
            try:
                self.retriever = HybridRetriever()
            except Exception as e:
                logger.warning(f"Could not auto-initialize HybridRetriever: {e}")
                self.retriever = None
        return self.retriever

    def _ensure_reranker(self) -> Optional[Reranker]:
        if self.enable_reranker and self.reranker is None:
            try:
                self.reranker = Reranker()
            except Exception as e:
                logger.warning(f"Could not auto-initialize Reranker: {e}")
                self.reranker = None
        return self.reranker

    def retrieve_evidence(
        self,
        query: str,
        top_k: int = 5,
        rerank_top_k: Optional[int] = None,
    ) -> Tuple[List[RetrievalResultItem], bool, List[str]]:
        """
        Retrieves top-k evidence chunks using two-stage hybrid search and re-ranking.
        Returns: (ranked_results, is_degraded, notices)
        """
        notices: List[str] = []
        retriever = self._ensure_retriever()
        if retriever is None:
            return [], True, ["Hybrid retriever unavailable; no document index found."]

        # 1. First-stage hybrid retrieval
        try:
            candidates = retriever.retrieve(query, top_k=max(top_k * 2, 10))
            is_degraded = getattr(retriever, "degraded", False)
            if hasattr(retriever, "notices") and retriever.notices:
                notices.extend(retriever.notices)
        except Exception as e:
            logger.error(f"Error during candidate retrieval: {e}")
            return [], True, [f"Candidate retrieval error: {str(e)}"]

        if not candidates:
            return [], is_degraded, notices

        # 2. Second-stage re-ranking
        reranker = self._ensure_reranker()
        final_k = rerank_top_k or top_k
        if reranker is not None:
            try:
                ranked = reranker.rerank(query, candidates, top_k=final_k)
                return ranked, is_degraded, notices
            except Exception as e:
                logger.warning(f"Re-ranker fallback to hybrid results: {e}")
                notices.append(f"Re-ranking failed ({str(e)}); falling back to hybrid rank.")

        # Fallback to candidates as RetrievalResultItems
        wrapped_candidates: List[RetrievalResultItem] = []
        for idx, c in enumerate(candidates[:final_k], start=1):
            if isinstance(c, RetrievalResultItem):
                wrapped_candidates.append(c)
            elif isinstance(c, EvidenceChunk):
                wrapped_candidates.append(
                    RetrievalResultItem(chunk=c, rank=idx, score=round(1.0 / idx, 4), retrieval_method="hybrid")
                )
            elif isinstance(c, dict):
                wrapped_candidates.append(
                    RetrievalResultItem(
                        chunk=EvidenceChunk(chunk_id=c.get("chunk_id", f"c_{idx}"), text=c.get("text", ""), metadata=c.get("metadata", {})),
                        rank=idx,
                        score=round(1.0 / idx, 4),
                        retrieval_method="hybrid",
                    )
                )

        return wrapped_candidates, is_degraded, notices

    def assess_risk(
        self,
        weather_snapshot: Any = None,
        disaster_snapshot: Any = None,
        transit_snapshot: Any = None,
        route_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[RiskAssessment, RouteInfo]:
        """
        Evaluates real-time risk scores and route accessibility using LocalRiskModel.
        """
        if self.risk_model is None:
            self.risk_model = LocalRiskModel()
        return self.risk_model.evaluate(
            weather_snapshot=weather_snapshot,
            disaster_snapshot=disaster_snapshot,
            transit_snapshot=transit_snapshot,
            route_context=route_context,
        )

    def get_risk_knowledge(
        self,
        query: str,
        top_k: int = 5,
        weather_snapshot: Any = None,
        disaster_snapshot: Any = None,
        transit_snapshot: Any = None,
        route_context: Optional[Dict[str, Any]] = None,
        evaluate_risk: bool = True,
    ) -> RiskKnowledgeResponse:
        """
        Complete knowledge service entrypoint.
        Retrieves verified safety evidence and assesses environmental/transit risk.
        Returns a canonical RiskKnowledgeResponse complying with the project contract.
        Applies in-memory caching and emergency-adaptive category prioritization.
        """
        cache_key = self._make_cache_key(
            query=query,
            top_k=top_k,
            weather_snapshot=weather_snapshot,
            disaster_snapshot=disaster_snapshot,
            transit_snapshot=transit_snapshot,
            route_context=route_context,
            evaluate_risk=evaluate_risk,
        )
        now_ts = time.time()
        if cache_key in self._cache:
            cached_resp, expires_at = self._cache[cache_key]
            if now_ts < expires_at:
                self._cache_hits += 1
                return cached_resp

        self._cache_misses += 1
        all_notices: List[str] = []

        # 1. Retrieve safety document evidence
        results, ret_degraded, ret_notices = self.retrieve_evidence(query=query, top_k=top_k)
        all_notices.extend(ret_notices)

        # 2. Local Risk Evaluation
        assessment: Optional[RiskAssessment] = None
        routes_info: Optional[RouteInfo] = None
        risk_degraded = False

        if evaluate_risk:
            assessment, routes_info = self.assess_risk(
                weather_snapshot=weather_snapshot,
                disaster_snapshot=disaster_snapshot,
                transit_snapshot=transit_snapshot,
                route_context=route_context,
            )
            if assessment.risk_level == RiskLevel.UNKNOWN:
                risk_degraded = True
                all_notices.append("Real-time risk feeds unavailable; risk assessment operating in degraded mode.")

        # 3. Adaptive Emergency Category Prioritization (Step 2.3)
        is_emergency_query = any(k in query.lower() for k in self.EMERGENCY_KEYWORDS)
        is_high_risk = assessment is not None and assessment.risk_level == RiskLevel.HIGH

        if (is_emergency_query or is_high_risk) and results:
            def _is_emergency_chunk(r: Any) -> bool:
                chunk = getattr(r, "chunk", r)
                meta = getattr(chunk, "metadata", {})
                if hasattr(meta, "category"):
                    cat = str(getattr(meta, "category", "") or "").lower()
                    sit = str(getattr(meta, "situation", "") or "").lower()
                elif isinstance(meta, dict):
                    cat = str(meta.get("category", "")).lower()
                    sit = str(meta.get("situation", "")).lower()
                else:
                    cat = ""
                    sit = ""
                text = str(getattr(chunk, "text", "") or "").lower()
                return (
                    any(c in cat for c in self.EMERGENCY_CATEGORIES)
                    or any(k in sit for k in self.EMERGENCY_KEYWORDS)
                    or any(k in text for k in ["119", "110", "hypothermia", "survival", "shelter"])
                )

            emergency_chunks = [r for r in results if _is_emergency_chunk(r)]
            other_chunks = [r for r in results if not _is_emergency_chunk(r)]
            reordered = emergency_chunks + other_chunks
            for idx, r in enumerate(reordered, start=1):
                if hasattr(r, "rank"):
                    r.rank = idx
            results = reordered
            if emergency_chunks:
                all_notices.append("Adaptive emergency filtering applied: prioritized life-safety and survival protocols.")

        total_degraded = ret_degraded or risk_degraded

        # Index version fingerprint
        index_version = ""
        if self.retriever and hasattr(self.retriever, "index_version"):
            index_version = getattr(self.retriever, "index_version", "")

        response = RiskKnowledgeResponse(
            results=results,
            risk_assessment=assessment,
            routes_info=routes_info,
            index_version=index_version,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            degraded=total_degraded,
            notices=all_notices,
        )

        # Store in cache
        self._cache[cache_key] = (response, now_ts + self.cache_ttl_seconds)
        return response
