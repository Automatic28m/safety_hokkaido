import unittest
import os
import sys

# Ensure module path is accessible
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from risk_knowledge.rerankers import Reranker
from risk_knowledge.models import RetrievalResultItem, EvidenceChunk, EvidenceChunkMetadata


class MockCrossEncoderModel:
    def predict(self, pairs):
        # Assign higher score if query word appears in text
        scores = []
        for query, text in pairs:
            if "blizzard" in query.lower() and "blizzard" in text.lower():
                scores.append(0.95)
            elif "shelter" in query.lower() and "shelter" in text.lower():
                scores.append(0.85)
            else:
                scores.append(0.30)
        return scores


class TestReranker(unittest.TestCase):
    def test_reranker_fallback_when_unavailable(self):
        reranker = Reranker()
        reranker.is_available = False
        reranker.model = None

        chunks = [{"text": "Sample chunk 1"}, {"text": "Sample chunk 2"}]
        reranked = reranker.rerank("test query", chunks, top_k=1)
        self.assertEqual(len(reranked), 1)
        self.assertEqual(reranked[0]["text"], "Sample chunk 1")

    def test_reranker_scoring_and_ordering(self):
        reranker = Reranker()
        reranker.model = MockCrossEncoderModel()
        reranker.is_available = True

        chunk_a = EvidenceChunk(
            chunk_id="c_general",
            text="General tourism in Sapporo clock tower."
        )
        chunk_b = EvidenceChunk(
            chunk_id="c_blizzard",
            text="Severe blizzard warning in Sapporo."
        )

        item_a = RetrievalResultItem(chunk=chunk_a, rank=1, score=0.5)
        item_b = RetrievalResultItem(chunk=chunk_b, rank=2, score=0.4)

        # Rerank with query targeting blizzard
        results = reranker.rerank("Sapporo blizzard safety", [item_a, item_b], top_k=2)
        self.assertEqual(len(results), 2)
        
        # chunk_b must be reranked to rank 1 with high score 0.95
        top_item = results[0]
        self.assertEqual(top_item.chunk.chunk_id, "c_blizzard")
        self.assertEqual(top_item.rank, 1)
        self.assertEqual(top_item.score, 0.95)
        self.assertEqual(top_item.retrieval_method, "hybrid+rerank")

        # chunk_a should be rank 2
        second_item = results[1]
        self.assertEqual(second_item.chunk.chunk_id, "c_general")
        self.assertEqual(second_item.rank, 2)
        self.assertEqual(second_item.score, 0.3)

    def test_reranker_with_raw_dicts(self):
        reranker = Reranker()
        reranker.model = MockCrossEncoderModel()
        reranker.is_available = True

        raw_chunks = [
            {"chunk_id": "c1", "text": "Low relevance note"},
            {"chunk_id": "c2", "text": "Emergency shelter protocol"}
        ]
        results = reranker.rerank("emergency shelter", raw_chunks, top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "c2")
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[0]["score"], 0.85)


if __name__ == "__main__":
    unittest.main()
