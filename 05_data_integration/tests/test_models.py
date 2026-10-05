import pytest
from data_integration.models import (
    ChunkMetadata,
    DocumentChunk,
    ChunkSettings,
    IndexManifest,
)


def test_chunk_metadata_defaults():
    meta = ChunkMetadata(
        source_file="test.pdf",
        category="Earthquake",
        situation="Tsunami Warning",
    )
    assert meta.source_file == "test.pdf"
    assert meta.category == "Earthquake"
    assert meta.situation == "Tsunami Warning"
    assert meta.url == "Local Document"
    assert meta.page is None
    assert meta.source_version == ""
    assert meta.reviewed_at == ""


def test_document_chunk_to_dict():
    meta = ChunkMetadata(
        source_file="guide.pdf",
        category="Winter Safety",
        situation="Blizzard Driving",
        url="https://example.com/guide",
        page=3,
        source_version="abc12345",
        reviewed_at="2026-09-24T00:00:00Z",
    )
    chunk = DocumentChunk(
        chunk_id="guide_p003_c001",
        text="Stay in your vehicle during whiteout conditions.",
        metadata=meta,
    )
    d = chunk.to_dict()

    assert d["chunk_id"] == "guide_p003_c001"
    assert d["text"] == "Stay in your vehicle during whiteout conditions."
    assert d["metadata"]["source_file"] == "guide.pdf"
    assert d["metadata"]["category"] == "Winter Safety"
    assert d["metadata"]["situation"] == "Blizzard Driving"
    assert d["metadata"]["url"] == "https://example.com/guide"
    assert d["metadata"]["page"] == 3
    assert d["metadata"]["source_version"] == "abc12345"
    assert d["metadata"]["reviewed_at"] == "2026-09-24T00:00:00Z"


def test_index_manifest_serialization():
    manifest = IndexManifest(
        schema_version="1.0.0",
        index_version="idx_test_001",
        corpus_hash="abcdef0123456789",
        embedding_model="all-MiniLM-L6-v2",
        chunk_settings={"chunk_size": 400, "chunk_overlap": 50},
        build_time="2026-09-24T12:00:00Z",
        total_chunks=150,
        total_sources=10,
        source_files=["doc1.pdf", "doc2.json"],
    )
    data = manifest.model_dump()
    assert data["schema_version"] == "1.0.0"
    assert data["total_chunks"] == 150
    assert len(data["source_files"]) == 2
