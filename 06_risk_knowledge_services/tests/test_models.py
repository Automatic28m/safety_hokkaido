import unittest
import json
import sys
import os

# Ensure module path is accessible
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from risk_knowledge.models import (
    RiskLevel,
    EvidenceChunkMetadata,
    EvidenceChunk,
    RetrievalResultItem,
    RetrievalRequest,
    RiskAssessment,
    RouteInfo,
    RiskKnowledgeResponse,
)


class TestRiskKnowledgeModels(unittest.TestCase):
    def test_evidence_chunk_metadata_provenance(self):
        meta = EvidenceChunkMetadata(
            source_file="jma_blizzard_protocol.pdf",
            category="blizzard_safety",
            situation="whiteout_driving",
            url="https://www.jma.go.jp/safety.html",
            page=4,
            source_version="a1b2c3d4e5f6",
            reviewed_at="2026-09-24T10:00:00Z"
        )
        self.assertEqual(meta.page, 4)
        self.assertEqual(meta.page_number, 4)
        self.assertEqual(meta["source_file"], "jma_blizzard_protocol.pdf")
        self.assertEqual(meta["page"], 4)

    def test_page_number_alias_sync(self):
        meta = EvidenceChunkMetadata(page_number=12)
        self.assertEqual(meta.page, 12)
        self.assertEqual(meta.page_number, 12)

    def test_evidence_chunk_serialization_and_subscript(self):
        chunk = EvidenceChunk(
            chunk_id="jma_blizzard_p004_c001",
            text="In severe whiteouts, pull over safely and keep hazard lights on.",
            metadata=EvidenceChunkMetadata(
                source_file="winter_guide.pdf",
                situation="whiteout",
                page=4
            )
        )
        data = chunk.to_dict()
        self.assertEqual(data["chunk_id"], "jma_blizzard_p004_c001")
        self.assertEqual(data["metadata"]["page"], 4)
        self.assertEqual(data["metadata"]["page_number"], 4)
        
        # Backward-compatible dict subscript access
        self.assertEqual(chunk["chunk_id"], "jma_blizzard_p004_c001")
        self.assertIn("pull over safely", chunk["text"])
        self.assertEqual(chunk["metadata"]["page"], 4)

    def test_retrieval_result_item(self):
        chunk = EvidenceChunk(
            chunk_id="chunk_01",
            text="Earthquake evacuation steps."
        )
        item = RetrievalResultItem(
            chunk=chunk,
            rank=1,
            score=0.925,
            retrieval_method="hybrid+rerank"
        )
        self.assertEqual(item.rank, 1)
        self.assertEqual(item.score, 0.925)
        self.assertEqual(item.retrieval_method, "hybrid+rerank")
        self.assertEqual(item["chunk"]["chunk_id"], "chunk_01")
        
        d = item.to_dict()
        self.assertIn("chunk", d)
        self.assertEqual(d["score"], 0.925)

    def test_retrieval_request_validation(self):
        req = RetrievalRequest(query="Sapporo heavy snow status", top_k=5)
        self.assertEqual(req.query, "Sapporo heavy snow status")
        self.assertEqual(req.top_k, 5)

    def test_risk_assessment_model(self):
        assessment = RiskAssessment(
            risk_level=RiskLevel.HIGH,
            risk_score=0.88,
            primary_factors=["Blizzard warning active", "Highway Route 5 closure"]
        )
        self.assertEqual(assessment.risk_level, RiskLevel.HIGH)
        self.assertEqual(assessment.risk_level.value, "HIGH")
        self.assertEqual(assessment.risk_score, 0.88)
        self.assertEqual(len(assessment.primary_factors), 2)
        
        d = assessment.to_dict()
        self.assertEqual(d["risk_level"], "HIGH")
        self.assertEqual(d["risk_score"], 0.88)

    def test_route_info_model(self):
        route = RouteInfo(
            recommended_route="Route 230 via Jozankei",
            alternative_routes=["Hakodate Main Line Local"],
            closed_segments=["Do-O Expressway (Sapporo-Otaru)"]
        )
        self.assertEqual(route.recommended_route, "Route 230 via Jozankei")
        self.assertEqual(len(route.closed_segments), 1)
        
        d = route.to_dict()
        self.assertIn("Do-O Expressway", d["closed_segments"][0])

    def test_risk_knowledge_response_json_serializability(self):
        chunk = EvidenceChunk(
            chunk_id="chunk_test",
            text="Official shelter location in Otaru.",
            metadata=EvidenceChunkMetadata(source_file="otaru_shelters.json", page=1)
        )
        result_item = RetrievalResultItem(chunk=chunk, rank=1, score=0.91)
        assessment = RiskAssessment(risk_level=RiskLevel.MEDIUM, risk_score=0.55)
        routes = RouteInfo(recommended_route="Route 5")

        resp = RiskKnowledgeResponse(
            results=[result_item],
            risk_assessment=assessment,
            routes_info=routes,
            index_version="2026.09.v1",
            degraded=False,
            notices=[]
        )
        
        dict_payload = resp.to_dict()
        # Verify complete JSON round-trip serialization without error
        json_str = json.dumps(dict_payload, ensure_ascii=False)
        self.assertIn("Official shelter location in Otaru.", json_str)
        self.assertIn('"risk_level": "MEDIUM"', json_str)
        self.assertIn('"degraded": false', json_str)


if __name__ == "__main__":
    unittest.main()
