import pytest

from agent_core import guardrails
from agent_core.schemas import ToolCall

ALL = {"weather": True, "disaster": True, "train": True}


def test_validate_route():
    assert guardrails.validate_route("rag+realtime") == "rag+realtime"
    with pytest.raises(guardrails.GuardrailViolation):
        guardrails.validate_route("browse")


def test_tool_disabled_by_caller_is_blocked():
    call = ToolCall(name="train", args={"line_name": "All"})
    with pytest.raises(guardrails.GuardrailViolation, match="disabled by the caller"):
        guardrails.validate_tool_args(call, {**ALL, "train": False}, ["weather", "disaster", "train"])


def test_tool_outside_allow_list_is_blocked():
    call = ToolCall(name="weather", args={"city": "Sapporo"})
    with pytest.raises(guardrails.GuardrailViolation, match="allow-list"):
        guardrails.validate_tool_args(call, ALL, ["disaster"])


def test_unsafe_argument_is_blocked_and_valid_argument_is_normalized():
    bad = ToolCall(name="weather", args={"city": "Sapporo; DROP TABLE"})
    with pytest.raises(guardrails.GuardrailViolation, match="invalid argument"):
        guardrails.validate_tool_args(bad, ALL, ["weather"])
    good = guardrails.validate_tool_args(ToolCall(name="weather", args={"city": "  Sapporo "}), ALL, ["weather"])
    assert good.args == {"city": "Sapporo"}
    region = guardrails.validate_tool_args(ToolCall(name="disaster", args={"region": None}), ALL, ["disaster"])
    assert region.args == {"region": "Hokkaido"}


def test_tool_result_status_notices():
    mocked, notices = guardrails.validate_tool_result("train", {"provider": "sim", "status": "mocked"})
    assert mocked["status"] == "mocked" and "simulated" in notices[0]
    bogus, notices = guardrails.validate_tool_result("weather", {"provider": "x", "status": "great"})
    assert bogus["status"] == "unavailable" and bogus["error_code"] == "INVALID_STATUS" and notices
    ok, notices = guardrails.validate_tool_result("weather", {"provider": "x", "status": "ok"})
    assert notices == [] and ok["fetched_at"] is None


def test_decision_html_stripped_and_unknown_references_dropped():
    decision = {
        "reply": "<script>alert(1)</script>Go <b>inside</b> now",
        "safety_level": "critical",
        "used_evidence_ids": ["chunk-1", "made-up"],
        "used_live_sources": ["jma", "ghost"],
        "degraded": False,
        "notices": ["n1", ""],
    }
    result, notices = guardrails.validate_decision(decision, ["chunk-1"], ["jma"], dependency_degraded=True)
    assert result.reply == "Go inside now"
    assert result.safety_level == "unknown"
    assert result.used_evidence_ids == ["chunk-1"] and result.used_live_sources == ["jma"]
    assert result.degraded is True
    assert result.notices == ["n1"]
    assert len(notices) == 3


def test_decision_empty_reply_is_rejected():
    with pytest.raises(guardrails.GuardrailViolation):
        guardrails.validate_decision({"reply": "<br>"}, [], [], dependency_degraded=False)
    with pytest.raises(guardrails.GuardrailViolation):
        guardrails.validate_decision({"reply": None}, [], [], dependency_degraded=False)
