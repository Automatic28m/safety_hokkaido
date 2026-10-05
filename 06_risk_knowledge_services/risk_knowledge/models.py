from typing import Optional, Dict, Any, List, Union
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class EvidenceChunkMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_file: str = Field(default="unknown", description="Name of the source document file")
    category: str = Field(default="general", description="Category or topic classification")
    situation: str = Field(default="", description="Specific situation context or headline")
    url: str = Field(default="Local Document", description="URL reference or source attribution")
    page: Optional[int] = Field(default=None, description="1-based page number in document")
    page_number: Optional[int] = Field(default=None, description="Alias for page for backward compatibility")
    source_version: str = Field(default="", description="Hash or version fingerprint of source file")
    reviewed_at: str = Field(default="", description="Timestamp or date when source was reviewed")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")

    def model_post_init(self, __context: Any) -> None:
        if self.page is not None and self.page_number is None:
            self.page_number = self.page
        elif self.page_number is not None and self.page is None:
            self.page = self.page_number

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


class EvidenceChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: str = Field(..., description="Stable, deterministic chunk identifier")
    text: str = Field(..., description="Cleaned chunk text content")
    metadata: EvidenceChunkMetadata = Field(
        default_factory=EvidenceChunkMetadata,
        description="Structured chunk metadata with provenance"
    )

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

    def __getitem__(self, item: str) -> Any:
        if item == "metadata":
            return self.metadata
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        if item == "metadata":
            return self.metadata
        return getattr(self, item, default)

    def __contains__(self, item: str) -> bool:
        return item in {"chunk_id", "text", "metadata"} or hasattr(self, item)


class RetrievalResultItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk: EvidenceChunk = Field(..., description="Retrieved evidence chunk")
    rank: int = Field(default=1, description="Rank position in final result list (1-based)")
    score: float = Field(default=0.0, description="Normalized relevance or cross-encoder score")
    retrieval_method: str = Field(
        default="hybrid+rerank",
        description="Retrieval method used (e.g. dense, sparse, hybrid, hybrid+rerank)"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk": self.chunk.to_dict(),
            "rank": self.rank,
            "score": self.score,
            "retrieval_method": self.retrieval_method,
        }

    def __getitem__(self, item: str) -> Any:
        if item == "chunk":
            return self.chunk
        if item == "text":
            return self.chunk.text
        if item == "metadata":
            return self.chunk.metadata
        if item == "chunk_id":
            return self.chunk.chunk_id
        if hasattr(self, item):
            return getattr(self, item)
        return self.chunk.get(item)

    def get(self, item: str, default: Any = None) -> Any:
        if item == "chunk":
            return self.chunk
        if item == "text":
            return self.chunk.text
        if item == "metadata":
            return self.chunk.metadata
        if item == "chunk_id":
            return self.chunk.chunk_id
        if hasattr(self, item):
            return getattr(self, item)
        return self.chunk.get(item, default)

    def __contains__(self, item: str) -> bool:
        if item in {"chunk", "rank", "score", "retrieval_method", "text", "metadata", "chunk_id"}:
            return True
        return hasattr(self, item) or (hasattr(self, "chunk") and item in self.chunk)


class RetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., description="Search query string")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to retrieve")
    index_version: Optional[str] = Field(default=None, description="Expected index version fingerprint")


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    risk_level: RiskLevel = Field(default=RiskLevel.UNKNOWN, description="Assessed risk level")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Numerical risk score (0.0 to 1.0)")
    primary_factors: List[str] = Field(default_factory=list, description="Key factors contributing to risk score")
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 evaluation timestamp"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "primary_factors": self.primary_factors,
            "evaluated_at": self.evaluated_at,
        }


class RouteInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recommended_route: Optional[str] = Field(default=None, description="Primary safe travel corridor")
    alternative_routes: List[str] = Field(default_factory=list, description="Viable alternative routes")
    closed_segments: List[str] = Field(default_factory=list, description="Reported closed highways or transit lines")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_route": self.recommended_route,
            "alternative_routes": self.alternative_routes,
            "closed_segments": self.closed_segments,
        }


class RiskKnowledgeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: List[RetrievalResultItem] = Field(default_factory=list, description="Ranked evidence chunks")
    risk_assessment: Optional[RiskAssessment] = Field(default=None, description="Route & area risk assessment")
    routes_info: Optional[RouteInfo] = Field(default=None, description="Route accessibility and closures")
    index_version: Optional[str] = Field(default="", description="Corpus index version fingerprint")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 response timestamp"
    )
    degraded: bool = Field(default=False, description="True if retrieval operated in degraded mode")
    notices: List[str] = Field(default_factory=list, description="Warnings or service status notices")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "routes_info": self.routes_info.to_dict() if self.routes_info else None,
            "index_version": self.index_version,
            "retrieved_at": self.retrieved_at,
            "degraded": self.degraded,
            "notices": self.notices,
        }
