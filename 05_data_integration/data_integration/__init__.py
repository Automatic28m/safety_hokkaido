"""
Safety Hokkaido — 05 Data Integration Module
Corpus ingestion, page provenance, text chunking, embeddings, and atomic index building.
"""

from data_integration.models import (
    ChunkMetadata,
    DocumentChunk,
    ChunkSettings,
    IndexManifest,
)
from data_integration.document_loader import (
    load_all_data,
    CorpusError,
    CorpusParseError,
    CorpusValidationError,
    compute_file_sha256,
)
from data_integration.text_splitter import TextSplitter
from data_integration.embedding_model import EmbeddingModel
from data_integration.index_meta import IndexMeta, load_manifest
from data_integration.vector_store import (
    VectorStore,
    VectorStoreError,
    VectorStoreBuildError,
)
from data_integration.builder import run_index_build, BuildResult

__all__ = [
    "ChunkMetadata",
    "DocumentChunk",
    "ChunkSettings",
    "IndexManifest",
    "load_all_data",
    "CorpusError",
    "CorpusParseError",
    "CorpusValidationError",
    "compute_file_sha256",
    "TextSplitter",
    "EmbeddingModel",
    "IndexMeta",
    "load_manifest",
    "VectorStore",
    "VectorStoreError",
    "VectorStoreBuildError",
    "run_index_build",
    "BuildResult",
]
