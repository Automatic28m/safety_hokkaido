"""Pydantic v2 request/response contracts for the FastAPI HTTP layer.

This module intentionally contains no orchestration, retrieval, or LLM logic -
it only describes and validates the shapes that cross the HTTP boundary.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ROUTES = {"general", "rag", "realtime", "rag+realtime"}


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """A single turn in a conversation, as sent by the web app."""

    model_config = ConfigDict(extra="ignore")

    role: Role
    content: str = Field(max_length=4000)

    @field_validator("role", mode="before")
    @classmethod
    def _coerce_legacy_role(cls, value: Any) -> Any:
        if value == "ai":
            return "assistant"
        return value


class ChatRequest(BaseModel):
    """The body accepted by POST /ask, covering both legacy and messages modes."""

    message: Optional[str] = None
    messages: Optional[List[ChatMessage]] = Field(default=None, max_length=50)
    enabled_agents: Optional[Dict[str, bool]] = None

    @model_validator(mode="after")
    def _validate_query(self) -> "ChatRequest":
        if self.messages is not None:
            if len(self.messages) == 0:
                raise ValueError("'messages' must not be empty.")
            last = self.messages[-1]
            if last.role != Role.USER:
                raise ValueError("The last item in 'messages' must have role 'user'.")
            if not last.content.strip():
                raise ValueError("The last message content must not be empty.")
        elif not self.message or not self.message.strip():
            raise ValueError("Request must include a non-empty 'message' or 'messages'.")
        return self

    @property
    def input_mode(self) -> str:
        return "messages" if self.messages is not None else "legacy"

    def build_enabled_agents(self) -> Dict[str, bool]:
        """Builds a fresh per-request dict; never shares state across requests."""
        agents = {"weather": True, "disaster": True, "train": True}
        if self.enabled_agents:
            for key, value in self.enabled_agents.items():
                if key in agents and value is False:
                    agents[key] = False
        return agents


class NormalizedAskRequest(BaseModel):
    """The normalized, JSON-serializable payload handed to node 03."""

    request_id: str
    original_query: str
    chat_history: List[Dict[str, str]]
    enabled_agents: Dict[str, bool]
    received_at: str
    input_mode: str


class AskResponse(BaseModel):
    reply: str
    request_id: str
    status: str = "ok"
    route: Optional[str] = None
    degraded: bool = False
    notices: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    live_sources: List[Dict[str, Any]] = Field(default_factory=list)


class ErrorResponse(AskResponse):
    detail: Any = None
    status: str = "error"
    degraded: bool = True
