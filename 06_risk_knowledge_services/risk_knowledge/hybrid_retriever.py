import os
import json
import pickle
from typing import List, Dict, Any, Optional, Union
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from .models import (
    EvidenceChunk,
    EvidenceChunkMetadata,
    RetrievalResultItem,
    RiskKnowledgeResponse,
)


class HybridRetriever:
    """
    Two-stage Hybrid Retriever combining FAISS Dense Vector Search,
    BM25 Sparse Lexical Search, and Reciprocal Rank Fusion (RRF).
    Supports provenance preservation (page number, source version, url)
    and graceful degradation if indices are unavailable.
    """

    def __init__(
        self,
        embedder=None,
        db_dir: Optional[str] = None,
        faiss_path: Optional[str] = None,
        bm25_path: Optional[str] = None,
        chunk_store_path: Optional[str] = None,
        meta_path: Optional[str] = None,
        use_hybrid: Optional[bool] = None,
        top_k: int = 10,
    ):
        self.embedder = embedder
        self.top_k = top_k
        self.use_hybrid = use_hybrid if use_hybrid is not None else True
        self.is_ready = False
        self.degraded = False
        self.notices: List[str] = []
        self.index_version = ""

        # Resolve directory paths
        if db_dir is None:
            # Try config from 02_api_backend if available
            try:
                from config import config
                self.db_dir = getattr(config, "DB_DIR", "vector_db")
                self.faiss_path = faiss_path or getattr(config, "FAISS_PATH", os.path.join(self.db_dir, "document.index"))
                self.bm25_path = bm25_path or getattr(config, "BM25_PATH", os.path.join(self.db_dir, "bm25_index.pkl"))
                self.chunk_store_path = chunk_store_path or getattr(config, "CHUNK_STORE_PATH", os.path.join(self.db_dir, "chunk_store.json"))
                if use_hybrid is None:
                    self.use_hybrid = getattr(config, "USE_HYBRID", True)
                if top_k == 10:
                    self.top_k = getattr(config, "RETRIEVER_TOP_K", 10)
            except ImportError:
                self.db_dir = "vector_db"
                self.faiss_path = faiss_path or os.path.join(self.db_dir, "document.index")
                self.bm25_path = bm25_path or os.path.join(self.db_dir, "bm25_index.pkl")
                self.chunk_store_path = chunk_store_path or os.path.join(self.db_dir, "chunk_store.json")
        else:
            self.db_dir = db_dir
            self.faiss_path = faiss_path or os.path.join(self.db_dir, "document.index")
            self.bm25_path = bm25_path or os.path.join(self.db_dir, "bm25_index.pkl")
            self.chunk_store_path = chunk_store_path or os.path.join(self.db_dir, "chunk_store.json")

        self.meta_path = meta_path or os.path.join(self.db_dir, "index_meta.json")

        self.faiss_index = None
        self.bm25 = None
        self.chunks: List[Dict[str, Any]] = []

        self._load_indices()

    def _load_indices(self) -> None:
        """Loads compiled FAISS index, BM25 index, and chunk store."""
        errors = []

        # 1. Load Chunks
        if os.path.exists(self.chunk_store_path):
            try:
                with open(self.chunk_store_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
            except Exception as e:
                errors.append(f"Failed to load chunk store from {self.chunk_store_path}: {e}")
        else:
            errors.append(f"Chunk store not found at {self.chunk_store_path}")

        # 2. Load FAISS Index
        if faiss is not None and os.path.exists(self.faiss_path):
            try:
                self.faiss_index = faiss.read_index(self.faiss_path)
            except Exception as e:
                errors.append(f"Failed to load FAISS index from {self.faiss_path}: {e}")
        else:
            errors.append(f"FAISS index not found or faiss library unavailable at {self.faiss_path}")

        # 3. Load BM25 Index
        if os.path.exists(self.bm25_path):
            try:
                with open(self.bm25_path, "rb") as f:
                    self.bm25 = pickle.load(f)
            except Exception as e:
                errors.append(f"Failed to load BM25 index from {self.bm25_path}: {e}")
        else:
            errors.append(f"BM25 index not found at {self.bm25_path}")

        # 4. Load Metadata Manifest if present
        if os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    self.index_version = meta.get("index_version", "")
            except Exception:
                pass

        if errors:
            self.is_ready = False
            self.degraded = True
            self.notices.extend(errors)
        else:
            self.is_ready = True
            self.degraded = False

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResultItem]:
        """
        Executes hybrid retrieval and returns structured RetrievalResultItem objects.
        Each item is fully backward-compatible with dict subscriptions (e.g. item['text'], item['metadata']).
        """
        k = top_k or self.top_k

        if not self.is_ready or not self.chunks:
            return []

        # 1. FAISS Dense Search
        dense_results: List[tuple[int, float]] = []
        if self.embedder is not None and self.faiss_index is not None:
            try:
                query_vector = self.embedder.encode([query])
                q_arr = np.array(query_vector).astype("float32")
                dists, indices = self.faiss_index.search(q_arr, min(k, len(self.chunks)))
                for i in range(len(indices[0])):
                    idx = int(indices[0][i])
                    if idx != -1 and idx < len(self.chunks):
                        score = float(dists[0][i])
                        dense_results.append((idx, score))
            except Exception as e:
                self.notices.append(f"Dense search encountered error: {e}")

        # If sparse search is disabled, return dense results directly
        if not self.use_hybrid or self.bm25 is None:
            items: List[RetrievalResultItem] = []
            for rank, (idx, dist) in enumerate(dense_results[:k], start=1):
                raw_chunk = self.chunks[idx]
                chunk_obj = self._build_evidence_chunk(raw_chunk)
                norm_score = round(1.0 / (1.0 + max(0.0, dist)), 4)
                items.append(
                    RetrievalResultItem(
                        chunk=chunk_obj,
                        rank=rank,
                        score=norm_score,
                        retrieval_method="dense",
                    )
                )
            return items

        # 2. BM25 Sparse Search
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        top_n = np.argsort(bm25_scores)[::-1][:k]

        sparse_results: List[tuple[int, float]] = []
        for idx in top_n:
            s = float(bm25_scores[idx])
            if s > 0:
                sparse_results.append((int(idx), s))

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_k = 60
        fused_scores: Dict[int, float] = {}

        for rank, (idx, _) in enumerate(dense_results):
            fused_scores[idx] = fused_scores.get(idx, 0.0) + 1.0 / (rrf_k + rank + 1)

        for rank, (idx, _) in enumerate(sparse_results):
            fused_scores[idx] = fused_scores.get(idx, 0.0) + 1.0 / (rrf_k + rank + 1)

        sorted_indices = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        final_indices = sorted_indices[:k]

        # Calculate max score for normalization
        max_rrf = max(fused_scores.values()) if fused_scores else 1.0

        items = []
        for rank, idx in enumerate(final_indices, start=1):
            raw_chunk = self.chunks[idx]
            chunk_obj = self._build_evidence_chunk(raw_chunk)
            norm_score = round(fused_scores[idx] / max_rrf, 4) if max_rrf > 0 else 0.0
            items.append(
                RetrievalResultItem(
                    chunk=chunk_obj,
                    rank=rank,
                    score=norm_score,
                    retrieval_method="hybrid",
                )
            )

        return items

    def retrieve_response(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> RiskKnowledgeResponse:
        """
        Executes hybrid retrieval and returns a fully packaged RiskKnowledgeResponse
        strictly following SAFETY_HOKKAIDO_NODE_CONTRACT.md.
        """
        results = self.retrieve(query, top_k=top_k)
        return RiskKnowledgeResponse(
            results=results,
            index_version=self.index_version,
            degraded=self.degraded,
            notices=list(self.notices),
        )

    def _build_evidence_chunk(self, raw_chunk: Dict[str, Any]) -> EvidenceChunk:
        """Maps a raw stored chunk dictionary to a structured EvidenceChunk model."""
        meta_dict = raw_chunk.get("metadata", {})
        if not isinstance(meta_dict, dict):
            meta_dict = {}

        page_val = meta_dict.get("page") or meta_dict.get("page_number")
        if page_val is not None:
            try:
                page_val = int(page_val)
            except (ValueError, TypeError):
                page_val = None

        metadata = EvidenceChunkMetadata(
            source_file=meta_dict.get("source_file", "unknown"),
            category=meta_dict.get("category", "general"),
            situation=meta_dict.get("situation", ""),
            url=meta_dict.get("url", "Local Document"),
            page=page_val,
            page_number=page_val,
            source_version=str(meta_dict.get("source_version", "")),
            reviewed_at=str(meta_dict.get("reviewed_at", "")),
            extra={k: v for k, v in meta_dict.items() if k not in {
                "source_file", "category", "situation", "url", "page", "page_number", "source_version", "reviewed_at"
            }}
        )

        return EvidenceChunk(
            chunk_id=str(raw_chunk.get("chunk_id", "chunk_unknown")),
            text=str(raw_chunk.get("text", "")),
            metadata=metadata,
        )
