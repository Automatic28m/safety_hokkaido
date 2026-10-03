import unittest
from datetime import datetime, timezone
import sys
import os

# Setup import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
pkg_root = os.path.abspath(os.path.join(current_dir, ".."))
workspace_root = os.path.abspath(os.path.join(pkg_root, ".."))
if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from risk_knowledge.models import (
    RiskLevel,
    EvidenceChunk,
    RetrievalResultItem,
    RiskAssessment,
    RouteInfo,
    RiskKnowledgeResponse,
)
from risk_knowledge.risk_model import LocalRiskModel
from risk_knowledge.risk_service import RiskKnowledgeService


class DummyRetriever:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.degraded = False
        self.notices = []
        self.index_version = "v1.0-mock"

    def retrieve(self, query: str, top_k: int = 5):
        if self.should_fail:
            raise RuntimeError("Database connection error")
        return [
            EvidenceChunk(
                chunk_id=f"doc_{i}",
                text=f"Safety guideline {i} for winter driving in Hokkaido.",
                metadata={"source_file": "winter_guide.pdf", "page": i, "situation": "blizzard"},
            )
            for i in range(1, top_k + 1)
        ]


class DummyReranker:
    def rerank(self, query: str, candidates: list, top_k: int = 5):
        ranked = []
        for idx, item in enumerate(candidates[:top_k], start=1):
            chunk = item.chunk if isinstance(item, RetrievalResultItem) else item
            ranked.append(
                RetrievalResultItem(
                    chunk=chunk,
                    rank=idx,
                    score=round(1.0 - (0.1 * idx), 2),
                    retrieval_method="cross-encoder",
                )
            )
        return ranked


class TestRiskKnowledgeService(unittest.TestCase):
    def setUp(self):
        self.retriever = DummyRetriever()
        self.reranker = DummyReranker()
        self.risk_model = LocalRiskModel()
        self.service = RiskKnowledgeService(
            retriever=self.retriever,
            reranker=self.reranker,
            risk_model=self.risk_model,
        )

    def test_retrieve_evidence_success(self):
        results, degraded, notices = self.service.retrieve_evidence("winter driving", top_k=3)
        self.assertEqual(len(results), 3)
        self.assertFalse(degraded)
        self.assertEqual(results[0].rank, 1)
        self.assertEqual(results[0].retrieval_method, "cross-encoder")
        self.assertEqual(results[0].chunk.metadata.page, 1)

    def test_assess_risk(self):
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": -16.0,
                    "summary": "Severe blizzard",
                    "wind_speed_ms": 22.0,
                    "precipitation_total_mm": 12.0,
                    "precipitation_type": "snow",
                }
            }
        }
        assessment, route_info = self.service.assess_risk(weather_snapshot=weather)
        self.assertEqual(assessment.risk_level, RiskLevel.HIGH)
        self.assertGreaterEqual(assessment.risk_score, 0.70)
        self.assertIsNotNone(route_info)

    def test_get_risk_knowledge_complete(self):
        weather = {
            "status": "ok",
            "data": {
                "current": {
                    "temperature_c": 5.0,
                    "summary": "Clear",
                    "wind_speed_ms": 2.0,
                    "precipitation_total_mm": 0.0,
                }
            }
        }
        response = self.service.get_risk_knowledge(
            query="Driving Sapporo to Otaru",
            top_k=2,
            weather_snapshot=weather,
            route_context={"origin": "Sapporo", "destination": "Otaru"},
        )

        self.assertIsInstance(response, RiskKnowledgeResponse)
        self.assertEqual(len(response.results), 2)
        self.assertIsNotNone(response.risk_assessment)
        self.assertEqual(response.risk_assessment.risk_level, RiskLevel.LOW)
        self.assertIsNotNone(response.routes_info)
        self.assertEqual(response.index_version, "v1.0-mock")
        self.assertFalse(response.degraded)

    def test_service_graceful_degradation_on_retriever_failure(self):
        failing_retriever = DummyRetriever(should_fail=True)
        service = RiskKnowledgeService(
            retriever=failing_retriever,
            reranker=self.reranker,
            risk_model=self.risk_model,
        )

        response = service.get_risk_knowledge(query="Test query", top_k=3)
        self.assertTrue(response.degraded)
        self.assertEqual(len(response.results), 0)
        self.assertTrue(any("error" in n.lower() or "fail" in n.lower() for n in response.notices))

    def test_service_evaluate_risk_disabled(self):
        response = self.service.get_risk_knowledge(
            query="General emergency hotline",
            top_k=2,
            evaluate_risk=False,
        )
        self.assertEqual(len(response.results), 2)
        self.assertIsNone(response.risk_assessment)
        self.assertIsNone(response.routes_info)


if __name__ == "__main__":
    unittest.main()
