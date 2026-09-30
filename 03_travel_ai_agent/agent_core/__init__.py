"""Node 03: intent routing, context management and agent orchestration.

Modules
-------
main.py             orchestrator entry point (``TravelAgent``)
schemas.py          data contracts crossing node boundaries
classifier.py       intent / route classification, language and slot detection
planner.py          execution plan, node 06 retrieval and node 04 tool loop
tools.py            allow-listed adapters from node 04
guardrails.py       validation gates before tools, after tools, after node 07
context_manager.py  per-conversation memory, query preparation, node 07 package
llm_client.py       the only provider client in the system
audit.py            privacy-minimized trace to node 08
"""

from agent_core.schemas import (
    OrchestrationRequest,
    OrchestrationResponse,
    RouteDecision,
    ToolCall,
    ToolResult,
)

__all__ = [
    "OrchestrationRequest",
    "OrchestrationResponse",
    "RouteDecision",
    "ToolCall",
    "ToolResult",
]
