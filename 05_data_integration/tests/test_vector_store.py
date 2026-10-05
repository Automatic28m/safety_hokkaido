import os
import pytest
import numpy as np

from data_integration.vector_store import VectorStore, VectorStoreBuildError
from data_integration.models import IndexManifest


def test_vector_store_build_and_atomic_swap(tmp_path):
    db_dir = tmp_path / "vector_db"
    store = VectorStore(db_dir=str(db_dir))

    assert not store.is_ready()

    chunks = [
        {
            "chunk_id": "test_c001",
            "text": "Watch out for black ice on Hokkaido roads.",
            "metadata": {
                "source_file": "winter.txt",
                "category": "Road",
                "situation": "Ice",
                "url": "Local",
                "page": None,
                "source_version": "v1",
                "reviewed_at": "2026-09-24",
            },
        }
    ]
    embeddings = np.random.randn(1, 384).astype("float32")

    manifest = IndexManifest(
        schema_version="1.0.0",
        index_version="idx_test_001",
        corpus_hash="hash12345",
        embedding_model="all-MiniLM-L6-v2",
        chunk_settings={"chunk_size": 400, "chunk_overlap": 50},
        build_time="2026-09-24T12:00:00Z",
        total_chunks=1,
        total_sources=1,
        source_files=["winter.txt"],
    )

    store.build_indexes(chunks=chunks, embeddings=embeddings, manifest=manifest)

    assert store.is_ready()
    loaded_chunks = store.load_chunks()
    assert len(loaded_chunks) == 1
    assert loaded_chunks[0]["chunk_id"] == "test_c001"

    loaded_manifest = store.load_manifest()
    assert loaded_manifest["index_version"] == "idx_test_001"

    # Ensure no lingering staging directories
    staging_dirs = [d for d in os.listdir(tmp_path) if ".staging" in d]
    assert len(staging_dirs) == 0


def test_vector_store_rollback_on_failure(tmp_path):
    db_dir = tmp_path / "vector_db"
    store = VectorStore(db_dir=str(db_dir))

    # Initial valid build
    chunks = [
        {
            "chunk_id": "init_c001",
            "text": "Initial advice",
            "metadata": {"source_file": "a.txt", "situation": "General"},
        }
    ]
    embeddings = np.random.randn(1, 384).astype("float32")
    store.build_indexes(chunks=chunks, embeddings=embeddings)
    assert store.is_ready()

    # Second build with mismatched dimensions/lengths -> should fail
    bad_chunks = [{"chunk_id": "c1", "text": "t1"}, {"chunk_id": "c2", "text": "t2"}]
    bad_embeddings = np.random.randn(1, 384).astype("float32")  # length mismatch: 2 vs 1

    with pytest.raises(VectorStoreBuildError):
        store.build_indexes(chunks=bad_chunks, embeddings=bad_embeddings)

    # Verify original index was preserved!
    assert store.is_ready()
    original_chunks = store.load_chunks()
    assert len(original_chunks) == 1
    assert original_chunks[0]["chunk_id"] == "init_c001"
