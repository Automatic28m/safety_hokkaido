import os
import glob
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from data_integration.document_loader import load_all_data
from data_integration.text_splitter import TextSplitter
from data_integration.embedding_model import EmbeddingModel
from data_integration.vector_store import VectorStore
from data_integration.index_meta import IndexMeta
from data_integration.models import IndexManifest


class BuildResult(BaseModel):
    success: bool
    skipped: bool = False
    total_chunks: int = 0
    total_sources: int = 0
    index_version: Optional[str] = None
    manifest: Optional[IndexManifest] = None
    error_message: Optional[str] = None


def run_index_build(
    data_dir: str,
    db_dir: str = "vector_db",
    chunk_size: int = 400,
    chunk_overlap: int = 50,
    embedding_model_name: str = "all-MiniLM-L6-v2",
    force_rebuild: bool = False,
    show_progress: bool = True,
) -> BuildResult:
    """
    Executes the complete data integration pipeline:
    1. Checks corpus freshness and staleness.
    2. Ingests and validates reviewed documents with page provenance (retaining page
       and page_number for all PDF chunks).
    3. Generates dense embeddings.
    4. Constructs FAISS, BM25, and canonical chunks with manifest.
    5. Publishes artifacts atomically.
    """
    chunk_settings = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
    meta_file = os.path.join(db_dir, "index_meta.json")
    meta = IndexMeta(
        data_dir=data_dir,
        meta_file=meta_file,
        chunk_settings=chunk_settings,
        embedding_model=embedding_model_name,
    )

    if not force_rebuild and not meta.is_stale(target_dir=db_dir):
        existing_manifest = meta.load_manifest(meta_file) if hasattr(meta, "load_manifest") else None
        return BuildResult(
            success=True,
            skipped=True,
            index_version=existing_manifest.index_version if existing_manifest else None,
            manifest=existing_manifest,
        )

    # 1. Ingestion
    splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = load_all_data(data_dir=data_dir, strict=True, splitter=splitter)

    if not chunks:
        return BuildResult(
            success=False,
            error_message="No valid chunks extracted from corpus.",
        )

    # Collect source list
    source_files = sorted(list({c["metadata"]["source_file"] for c in chunks}))

    # 2. Embedding
    embedder = EmbeddingModel(model_name=embedding_model_name)
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=show_progress)

    # 3. Manifest Construction
    manifest = meta.build_manifest(
        total_chunks=len(chunks),
        total_sources=len(source_files),
        source_files=source_files,
        embedding_model=embedding_model_name,
        chunk_settings=chunk_settings,
    )

    # 4. Atomic Vector Store Build
    store = VectorStore(db_dir=db_dir)
    store.build_indexes(chunks=chunks, embeddings=embeddings, manifest=manifest)

    return BuildResult(
        success=True,
        skipped=False,
        total_chunks=len(chunks),
        total_sources=len(source_files),
        index_version=manifest.index_version,
        manifest=manifest,
    )
