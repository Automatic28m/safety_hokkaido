import unittest
import json
import pickle
import os
import sys
import tempfile
import shutil
import numpy as np

# Ensure module path is accessible
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from rank_bm25 import BM25Okapi
import faiss

from risk_knowledge.hybrid_retriever import HybridRetriever
from risk_knowledge.models import RetrievalResultItem, RiskKnowledgeResponse


class DummyEmbedder:
    def encode(self, texts):
        return np.ones((len(texts), 4), dtype=np.float32)


class TestHybridRetriever(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.faiss_path = os.path.join(self.test_dir, "document.index")
        self.bm25_path = os.path.join(self.test_dir, "bm25_index.pkl")
        self.chunk_store_path = os.path.join(self.test_dir, "chunk_store.json")
        self.meta_path = os.path.join(self.test_dir, "index_meta.json")

        self.sample_chunks = [
            {
                "chunk_id": "jma_blizzard_p001_c001",
                "text": "Sapporo blizzard warning. Visibility is near zero on expressways.",
                "metadata": {
                    "source_file": "blizzard_safety.pdf",
                    "category": "blizzard",
                    "situation": "whiteout_driving",
                    "url": "https://www.jma.go.jp",
                    "page": 1,
                    "source_version": "v1_hash",
                    "reviewed_at": "2026-09-24T00:00:00Z"
                }
            },
            {
                "chunk_id": "jma_earthquake_p002_c001",
                "text": "Otaru earthquake evacuation protocol and shelter locations.",
                "metadata": {
                    "source_file": "earthquake_safety.pdf",
                    "category": "earthquake",
                    "situation": "shelter_evacuation",
                    "url": "https://www.jma.go.jp",
                    "page": 2,
                    "source_version": "v2_hash",
                    "reviewed_at": "2026-09-24T00:00:00Z"
                }
            }
        ]

        # 1. Save chunks
        with open(self.chunk_store_path, "w", encoding="utf-8") as f:
            json.dump(self.sample_chunks, f)

        # 2. Build and save FAISS index
        d = 4
        index = faiss.IndexFlatL2(d)
        vectors = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=np.float32)
        index.add(vectors)
        faiss.write_index(index, self.faiss_path)

        # 3. Build and save BM25
        corpus = [c["text"].lower().split() for c in self.sample_chunks]
        bm25 = BM25Okapi(corpus)
        with open(self.bm25_path, "wb") as f:
            pickle.dump(bm25, f)

        # 4. Save metadata manifest
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump({"index_version": "2026.09.test"}, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_missing_indices_graceful_degradation(self):
        retriever = HybridRetriever(
            embedder=DummyEmbedder(),
            db_dir="/non/existent/path/for/testing"
        )
        self.assertFalse(retriever.is_ready)
        self.assertTrue(retriever.degraded)
        self.assertGreater(len(retriever.notices), 0)
        # Does not crash, returns empty list
        results = retriever.retrieve("blizzard")
        self.assertEqual(results, [])

    def test_successful_hybrid_retrieval(self):
        retriever = HybridRetriever(
            embedder=DummyEmbedder(),
            db_dir=self.test_dir,
            top_k=2
        )
        self.assertTrue(retriever.is_ready)
        self.assertFalse(retriever.degraded)

        results = retriever.retrieve("Sapporo blizzard")
        self.assertGreater(len(results), 0)
        top_item = results[0]

        # Verify model structure
        self.assertIsInstance(top_item, RetrievalResultItem)
        self.assertEqual(top_item.rank, 1)
        self.assertGreaterEqual(top_item.score, 0.0)
        self.assertEqual(top_item.retrieval_method, "hybrid")

        # Verify page provenance and metadata
        self.assertEqual(top_item.chunk.metadata.page, 1)
        self.assertEqual(top_item.chunk.metadata.page_number, 1)
        self.assertEqual(top_item.chunk.metadata.source_file, "blizzard_safety.pdf")

    def test_backward_compatibility_dict_access(self):
        retriever = HybridRetriever(
            embedder=DummyEmbedder(),
            db_dir=self.test_dir,
            top_k=2
        )
        results = retriever.retrieve("earthquake shelter")
        self.assertGreater(len(results), 0)
        first = results[0]

        # Callers expecting dictionary access directly on the result item
        self.assertIn("text", first)
        self.assertIn("metadata", first)
        self.assertIsNotNone(first["text"])
        self.assertIsNotNone(first["metadata"]["situation"])
        self.assertEqual(first.get("text"), first["text"])

    def test_retrieve_response_envelope(self):
        retriever = HybridRetriever(
            embedder=DummyEmbedder(),
            db_dir=self.test_dir
        )
        resp = retriever.retrieve_response("blizzard", top_k=1)
        self.assertIsInstance(resp, RiskKnowledgeResponse)
        self.assertEqual(resp.index_version, "2026.09.test")
        self.assertFalse(resp.degraded)
        
        # Verify JSON serialization
        d = resp.to_dict()
        self.assertIn("results", d)
        self.assertEqual(len(d["results"]), 1)


if __name__ == "__main__":
    unittest.main()
