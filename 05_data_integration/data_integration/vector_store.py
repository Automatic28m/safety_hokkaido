import os
import uuid
import json
import shutil
import pickle
from typing import List, Dict, Any, Optional

import numpy as np
import faiss
from rank_bm25 import BM25Okapi

from data_integration.models import IndexManifest


class VectorStoreError(Exception):
    """Base exception for vector store operations."""
    pass


class VectorStoreBuildError(VectorStoreError):
    """Raised when index building or verification fails."""
    pass


class VectorStore:
    def __init__(self, db_dir: str = "vector_db"):
        self.db_dir = db_dir
        self.faiss_path = os.path.join(self.db_dir, "document.index")
        self.bm25_path = os.path.join(self.db_dir, "bm25_index.pkl")
        self.chunk_store_path = os.path.join(self.db_dir, "chunk_store.json")
        self.meta_path = os.path.join(self.db_dir, "index_meta.json")

    def build_indexes(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: np.ndarray,
        manifest: Optional[IndexManifest] = None,
    ) -> None:
        """
        Builds FAISS, BM25, chunk store, and manifest atomically in a staging
        directory before swapping into production, preventing partial artifacts.
        """
        if len(chunks) == 0:
            raise VectorStoreBuildError("Cannot build indexes with 0 chunks.")

        if len(chunks) != len(embeddings):
            raise VectorStoreBuildError(
                f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings."
            )

        parent_dir = os.path.dirname(os.path.abspath(self.db_dir))
        os.makedirs(parent_dir, exist_ok=True)

        staging_dir = os.path.join(
            parent_dir, f".staging_{os.path.basename(self.db_dir)}_{uuid.uuid4().hex[:8]}"
        )
        os.makedirs(staging_dir, exist_ok=True)

        stg_faiss = os.path.join(staging_dir, "document.index")
        stg_bm25 = os.path.join(staging_dir, "bm25_index.pkl")
        stg_chunks = os.path.join(staging_dir, "chunk_store.json")
        stg_meta = os.path.join(staging_dir, "index_meta.json")

        try:
            # 1. Build FAISS dense index
            dimension = embeddings.shape[1]
            faiss_index = faiss.IndexFlatL2(dimension)
            faiss_index.add(np.array(embeddings).astype("float32"))
            faiss.write_index(faiss_index, stg_faiss)

            # 2. Build BM25 sparse index
            tokenized_corpus = [chunk["text"].lower().split() for chunk in chunks]
            bm25 = BM25Okapi(tokenized_corpus)
            with open(stg_bm25, "wb") as f:
                pickle.dump(bm25, f)

            # 3. Save canonical chunk store
            with open(stg_chunks, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)

            # 4. Save manifest
            if manifest:
                meta_dict = {
                    "data_hash": manifest.corpus_hash,  # Backward compatibility
                    **manifest.model_dump(),
                }
            else:
                meta_dict = {
                    "schema_version": "1.0.0",
                    "total_chunks": len(chunks),
                    "dimension": dimension,
                }
            with open(stg_meta, "w", encoding="utf-8") as f:
                json.dump(meta_dict, f, indent=2, ensure_ascii=False)

            # 5. Verification step: Ensure all 4 files are valid and loadable
            self._verify_artifacts(stg_faiss, stg_bm25, stg_chunks, stg_meta, len(chunks))

            # 6. Atomic swap into target directory
            self._atomic_swap(staging_dir)

        except Exception as e:
            # Clean up staging on failure, leaving existing db_dir intact
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)
            raise VectorStoreBuildError(f"Index build failed: {e}") from e

    def _verify_artifacts(
        self,
        faiss_p: str,
        bm25_p: str,
        chunks_p: str,
        meta_p: str,
        expected_chunks: int,
    ) -> None:
        """Verifies integrity of all staged artifacts before publication."""
        for p in [faiss_p, bm25_p, chunks_p, meta_p]:
            if not os.path.exists(p) or os.path.getsize(p) == 0:
                raise VectorStoreBuildError(f"Missing or empty artifact: {os.path.basename(p)}")

        # Verify FAISS readable
        idx = faiss.read_index(faiss_p)
        if idx.ntotal != expected_chunks:
            raise VectorStoreBuildError(
                f"FAISS count mismatch: expected {expected_chunks}, got {idx.ntotal}"
            )

        # Verify chunks loadable
        with open(chunks_p, "r", encoding="utf-8") as f:
            loaded_chunks = json.load(f)
        if len(loaded_chunks) != expected_chunks:
            raise VectorStoreBuildError("Chunk store count mismatch.")

        # Verify BM25 unpicklable
        with open(bm25_p, "rb") as f:
            pickle.load(f)

    def _atomic_swap(self, staging_dir: str) -> None:
        """Safely swaps staging directory into target db_dir."""
        backup_dir = None
        target_path = os.path.abspath(self.db_dir)

        try:
            if os.path.exists(target_path):
                backup_dir = f"{target_path}_backup_{uuid.uuid4().hex[:8]}"
                os.rename(target_path, backup_dir)

            os.rename(staging_dir, target_path)

            if backup_dir and os.path.exists(backup_dir):
                shutil.rmtree(backup_dir, ignore_errors=True)

        except Exception as swap_err:
            # Attempt rollback
            if backup_dir and os.path.exists(backup_dir) and not os.path.exists(target_path):
                os.rename(backup_dir, target_path)
            raise VectorStoreBuildError(f"Atomic swap failed: {swap_err}") from swap_err

    def is_ready(self) -> bool:
        """Checks if all 4 required artifacts exist in the database directory."""
        required = [self.faiss_path, self.bm25_path, self.chunk_store_path, self.meta_path]
        return all(os.path.exists(p) and os.path.getsize(p) > 0 for p in required)

    def load_chunks(self) -> List[Dict[str, Any]]:
        """Loads canonical chunk records."""
        with open(self.chunk_store_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_manifest(self) -> Optional[Dict[str, Any]]:
        """Loads index manifest metadata."""
        if not os.path.exists(self.meta_path):
            return None
        with open(self.meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
