import pytest
from pydantic import ValidationError

from agent_core.schemas import (
    AuditEvent,
    OrchestrationRequest,
    OrchestrationResponse,
    RouteDecision,
    ToolCall,
    ToolResult,
)


def test_request_builds_fresh_enabled_agents_with_missing_keys_enabled():
    request = OrchestrationRequest(request_id="r1", original_query="hi", enabled_agents={"weather": False})
    assert request.enabled_agents == {"weather": False, "disaster": True, "train": True}


def test_request_ignores_unknown_agents_and_non_false_values():
    request = OrchestrationRequest(
        request_id="r1", original_query="hi", enabled_agents={"made_up": False, "train": "no"}
    )
    assert request.enabled_agents == {"weather": True, "disaster": True, "train": True}


def test_request_rejects_blank_query():
    with pytest.raises(ValidationError):
        OrchestrationRequest(request_id="r1", original_query="   ")


def test_request_accepts_node02_normalized_payload_shape():
    payload = {
        "request_id": "abc",
        "original_query": "q",
        "chat_history": [{"role": "user", "content": "q"}],
        "enabled_agents": {"weather": True, "disaster": True, "train": True},
        "received_at": "2026-09-26T00:00:00+00:00",
        "input_mode": "messages",
        "unexpected": "ignored",
    }
    request = OrchestrationRequest.from_normalized(payload)
    assert request.input_mode == "messages"
    assert request.conversation_id is None


def test_route_decision_rejects_unknown_route():
    with pytest.raises(ValidationError):
        RouteDecision(route="not-a-route")


def test_route_decision_drops_unknown_tool_hints():
    decision = RouteDecision(route="realtime", tool_hints=["weather", "bogus"])
    assert decision.tool_hints == ["weather"]
    assert decision.needs_live_data and not decision.needs_retrieval


def test_tool_call_rejects_unknown_tool():
    with pytest.raises(ValidationError):
        ToolCall(name="browser", args={})


def test_tool_result_public_view_omits_raw_data():
    result = ToolResult(
        call=ToolCall(name="weather", args={"city": "Sapporo"}),
        snapshot={"provider": "meteosource", "status": "ok", "data": {"secret": 1}, "fetched_at": "t"},
    )
    view = result.public_view()
    assert view["provider"] == "meteosource" and view["tool"] == "weather"
    assert "data" not in view


def test_unavailable_response_is_always_degraded():
    response = OrchestrationResponse(status="unavailable", request_id="r1")
    assert response.degraded is True


def test_audit_event_payload_drops_missing_index_version_and_forbids_extra():
    event = AuditEvent(request_id="r1", timestamp="2026-09-26T00:00:00Z", route="rag", degraded=False)
    assert "index_version" not in event.to_payload()
    with pytest.raises(ValidationError):
        AuditEvent(request_id="r1", timestamp="t", route="rag", degraded=False, query="secret")
