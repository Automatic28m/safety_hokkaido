from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    source_file: str = Field(..., description="Name of the source document file")
    category: str = Field(..., description="Category or topic classification")
    situation: str = Field(..., description="Specific situation context or headline")
    url: str = Field(default="Local Document", description="URL reference or source attribution")
    page: Optional[int] = Field(default=None, description="1-based page number for paginated documents (e.g. PDF)")
    page_number: Optional[int] = Field(default=None, description="Alias for page for backward compatibility")
    source_version: str = Field(default="", description="Hash or version fingerprint of source file")
    reviewed_at: str = Field(default="", description="Timestamp or date when source was reviewed")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")

    model_config = {
        "extra": "ignore"
    }

    def model_post_init(self, __context: Any) -> None:
        if self.page is not None and self.page_number is None:
            self.page_number = self.page
        elif self.page_number is not None and self.page is None:
            self.page = self.page_number


class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="Stable, deterministic chunk identifier")
    text: str = Field(..., description="Cleaned chunk text content")
    metadata: ChunkMetadata = Field(..., description="Structured chunk metadata")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": {
                "source_file": self.metadata.source_file,
                "category": self.metadata.category,
                "situation": self.metadata.situation,
                "url": self.metadata.url,
                "page": self.metadata.page,
                "page_number": self.metadata.page,
                "source_version": self.metadata.source_version,
                "reviewed_at": self.metadata.reviewed_at,
                **self.metadata.extra,
            },
        }


class ChunkSettings(BaseModel):
    chunk_size: int = Field(default=400, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Chunk overlap in characters")


class IndexManifest(BaseModel):
    schema_version: str = Field(default="1.0.0", description="Index schema contract version")
    index_version: str = Field(..., description="Unique fingerprint identifier for this build")
    corpus_hash: str = Field(..., description="Combined cryptographic hash of reviewed corpus")
    embedding_model: str = Field(..., description="Name of the embedding model used")
    chunk_settings: Dict[str, int] = Field(..., description="Chunk size and overlap settings")
    build_time: str = Field(..., description="ISO 8601 build timestamp")
    total_chunks: int = Field(..., description="Total count of indexed chunks")
    total_sources: int = Field(..., description="Total count of processed source documents")
    source_files: List[str] = Field(default_factory=list, description="List of source file names included")
