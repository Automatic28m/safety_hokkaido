"""Data contracts for node 03 (travel AI agent / orchestration).

Every object that crosses a boundary inside node 03, or between node 03 and
nodes 02, 04, 06, 07 and 08, is described here. The module contains no
orchestration logic and performs no network calls.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ROUTES = ("general", "rag", "realtime", "rag+realtime")
RETRIEVAL_ROUTES = ("rag", "rag+realtime")
LIVE_DATA_ROUTES = ("realtime", "rag+realtime")

TOOL_NAMES = ("weather", "disaster", "train")

SNAPSHOT_STATUSES = ("ok", "partial", "stale", "unavailable", "mocked")
SAFETY_LEVELS = ("unknown", "advisory", "urgent")

RESPONSE_STATUS_OK = "ok"
RESPONSE_STATUS_UNAVAILABLE = "unavailable"

EVALUATION_SCHEMA_VERSION = "1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_enabled_agents() -> Dict[str, bool]:
    return {name: True for name in TOOL_NAMES}


class OrchestrationRequest(BaseModel):
    """Validated request handed to node 03 by node 02.

    ``chat_history`` coming from the API is authoritative. Server-side memory is
    consulted only when the client did not send a history and a
    ``conversation_id`` is present.
    """

    model_config = ConfigDict(extra="ignore")

    request_id: str = Field(min_length=1)
    conversation_id: Optional[str] = None
    original_query: str
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    enabled_agents: Dict[str, bool] = Field(default_factory=default_enabled_agents)
    locale: Optional[str] = None
    received_at: str = Field(default_factory=utc_now_iso)
    input_mode: str = "legacy"

    @field_validator("original_query")
    @classmethod
    def _query_not_blank(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("original_query must be a non-empty string")
        return value

    @field_validator("enabled_agents", mode="before")
    @classmethod
    def _normalize_enabled_agents(cls, value: Any) -> Dict[str, bool]:
        agents = default_enabled_agents()
        if isinstance(value, dict):
            for key, flag in value.items():
                if key in agents and flag is False:
                    agents[key] = False
        return agents

    @field_validator("chat_history", mode="before")
    @classmethod
    def _coerce_history(cls, value: Any) -> List[Dict[str, str]]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("chat_history must be a list")
        return value

    @classmethod
    def from_normalized(cls, payload: Dict[str, Any]) -> "OrchestrationRequest":
        """Builds a request from node 02's ``NormalizedAskRequest`` dump."""
        return cls(**payload)


class RouteDecision(BaseModel):
    """Result of intent classification (classifier.py)."""

    model_config = ConfigDict(extra="ignore")

    route: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""
    fallback_used: bool = False
    source: str = "llm"  # llm | keyword | default
    tool_hints: List[str] = Field(default_factory=list)

    @field_validator("route")
    @classmethod
    def _route_in_enum(cls, value: str) -> str:
        if value not in ROUTES:
            raise ValueError(f"route must be one of {ROUTES}")
        return value

    @field_validator("tool_hints")
    @classmethod
    def _hints_known(cls, value: List[str]) -> List[str]:
        return [hint for hint in value if hint in TOOL_NAMES]

    @property
    def needs_retrieval(self) -> bool:
        return self.route in RETRIEVAL_ROUTES

    @property
    def needs_live_data(self) -> bool:
        return self.route in LIVE_DATA_ROUTES


class ToolCall(BaseModel):
    """A single validated call to a node 04 adapter."""

    model_config = ConfigDict(extra="ignore")

    name: str
    args: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _known_tool(cls, value: str) -> str:
        if value not in TOOL_NAMES:
            raise ValueError(f"unknown tool '{value}'")
        return value


class ToolResult(BaseModel):
    """A node 04 ``LiveDataSnapshot`` (as a dict) paired with the call that produced it."""

    model_config = ConfigDict(extra="ignore")

    call: ToolCall
    snapshot: Dict[str, Any]
    notices: List[str] = Field(default_factory=list)

    @property
    def status(self) -> str:
        return str(self.snapshot.get("status", "unavailable"))

    @property
    def provider(self) -> str:
        return str(self.snapshot.get("provider", self.call.name))

    def public_view(self) -> Dict[str, Any]:
        """Provenance-only view returned to node 02 (raw provider payload omitted)."""
        keys = ("provider", "kind", "scope", "status", "fetched_at", "expires_at",
                "source_url", "error_code", "notice")
        view = {key: self.snapshot.get(key) for key in keys}
        view["tool"] = self.call.name
        return view


class ExecutionPlan(BaseModel):
    """What the planner decided to do for one request."""

    model_config = ConfigDict(extra="ignore")

    route: str
    needs_retrieval: bool = False
    retrieval_query: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    skipped_tools: Dict[str, str] = Field(default_factory=dict)
    notices: List[str] = Field(default_factory=list)


class ContextPackage(BaseModel):
    """Everything node 07 receives. Nothing else is sent to the decision layer."""

    model_config = ConfigDict(extra="ignore")

    original_query: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    live_data: List[Dict[str, Any]] = Field(default_factory=list)
    language: str = "en"
    tool_policy: Dict[str, Any] = Field(default_factory=dict)
    route: str = "general"


class DecisionResult(BaseModel):
    """Structured decision returned by node 07 after guardrail validation."""

    model_config = ConfigDict(extra="ignore")

    reply: str
    safety_level: str = "unknown"
    used_evidence_ids: List[str] = Field(default_factory=list)
    used_live_sources: List[str] = Field(default_factory=list)
    degraded: bool = False
    notices: List[str] = Field(default_factory=list)

    @field_validator("safety_level", mode="before")
    @classmethod
    def _safety_level_enum(cls, value: Any) -> str:
        return value if value in SAFETY_LEVELS else "unknown"


class OrchestrationResponse(BaseModel):
    """What node 03 returns to node 02 (``ask_structured``)."""

    model_config = ConfigDict(extra="ignore")

    status: str = RESPONSE_STATUS_OK
    reply: str = ""
    request_id: str
    route: Optional[str] = None
    degraded: bool = False
    notices: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    live_sources: List[Dict[str, Any]] = Field(default_factory=list)
    safety_level: str = "unknown"
    fallback_used: bool = False
    language: str = "en"
    used_evidence_ids: List[str] = Field(default_factory=list)
    used_live_sources: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unavailable_is_degraded(self) -> "OrchestrationResponse":
        if self.status == RESPONSE_STATUS_UNAVAILABLE:
            self.degraded = True
        return self


class AuditEvent(BaseModel):
    """Privacy-minimized trace sent to node 08 after an answer (no query text)."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    timestamp: str
    route: str
    degraded: bool
    evidence_ids: List[str] = Field(default_factory=list)
    source_versions: List[str] = Field(default_factory=list)
    evaluation_schema_version: str = EVALUATION_SCHEMA_VERSION
    index_version: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        if payload.get("index_version") is None:
            payload.pop("index_version")
        return payload
