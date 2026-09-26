"""Safety and validation gates for node 03.

Guardrails validate; they never decide whether a situation is safe. They sit at
three points of the flow: before a tool is called, after a tool returns, and
after node 07 returns a decision.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from agent_core.schemas import (
    ROUTES,
    SAFETY_LEVELS,
    SNAPSHOT_STATUSES,
    TOOL_NAMES,
    DecisionResult,
    ToolCall,
)

try:  # node 04 owns the argument validators; fall back to a strict local check
    from external_data.validation import validate_city, validate_line_name, validate_region
except Exception:  # pragma: no cover - node 04 absent or broken
    validate_city = validate_line_name = validate_region = None  # type: ignore

_LOCAL_UNSAFE = re.compile(r"[\r\n\t\x00-\x1f\x7f<>{}|\\^~\[\]`;/?:@&=+$]")
_HTML_TAG = re.compile(r"<[^>]+>")
_SCRIPT_BLOCK = re.compile(r"<script.*?</script>", re.DOTALL | re.IGNORECASE)
_MAX_REPLY_CHARS = 8000


class GuardrailViolation(Exception):
    """Raised when a route, a tool call or a decision fails validation and must not proceed."""


def validate_route(route: Any) -> str:
    if route not in ROUTES:
        raise GuardrailViolation(f"route '{route}' is not in {ROUTES}")
    return route


def _local_arg_check(value: Any, max_len: int) -> Tuple[bool, str, Optional[str]]:
    if not isinstance(value, str) or not value.strip():
        return False, "", "argument must be a non-empty string"
    cleaned = value.strip()
    if len(cleaned) > max_len:
        return False, "", "argument is too long"
    if _LOCAL_UNSAFE.search(cleaned):
        return False, "", "argument contains unsafe characters"
    return True, cleaned, None


def validate_tool_args(
    call: ToolCall,
    enabled_agents: Dict[str, bool],
    allowed_tools: Iterable[str],
) -> ToolCall:
    """Checks the allow-list, the caller's toggles and the argument format."""
    if call.name not in TOOL_NAMES:
        raise GuardrailViolation(f"tool '{call.name}' is unknown")
    if call.name not in set(allowed_tools):
        raise GuardrailViolation(f"tool '{call.name}' is not on the allow-list")
    if enabled_agents.get(call.name, True) is False:
        raise GuardrailViolation(f"tool '{call.name}' was disabled by the caller")

    if call.name == "weather":
        value = call.args.get("city")
        ok, cleaned, err = validate_city(value) if validate_city else _local_arg_check(value, 60)
        key = "city"
    elif call.name == "disaster":
        value = call.args.get("region")
        ok, cleaned, err = validate_region(value) if validate_region else _local_arg_check(value, 60)
        key = "region"
    else:
        value = call.args.get("line_name")
        ok, cleaned, err = validate_line_name(value) if validate_line_name else _local_arg_check(value, 80)
        key = "line_name"

    if not ok:
        raise GuardrailViolation(f"invalid argument for '{call.name}': {err}")
    return ToolCall(name=call.name, args={key: cleaned})


def validate_tool_result(tool: str, snapshot: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Normalizes a node 04 snapshot and produces user-facing notices."""
    notices: List[str] = []
    result = dict(snapshot or {})

    for key in ("provider", "kind", "scope", "fetched_at"):
        result.setdefault(key, None)
    status = result.get("status")
    if status not in SNAPSHOT_STATUSES:
        result["status"] = "unavailable"
        result.setdefault("error_code", "INVALID_STATUS")
        status = "unavailable"

    provider = result.get("provider") or tool
    if status == "mocked":
        notices.append(f"{provider}: simulated data, not an official live source.")
    elif status == "stale":
        notices.append(f"{provider}: data is older than its freshness window.")
    elif status == "partial":
        notices.append(f"{provider}: provider returned incomplete data.")
    elif status == "unavailable":
        reason = result.get("error_code") or "unknown"
        notices.append(f"{provider}: live data unavailable ({reason}).")

    return result, notices


def sanitize_markdown(text: str) -> Tuple[str, bool]:
    """Strips HTML/script and caps the length. Returns (text, was_truncated)."""
    text = _SCRIPT_BLOCK.sub("", text)
    text = _HTML_TAG.sub("", text).strip()
    if len(text) > _MAX_REPLY_CHARS:
        return text[:_MAX_REPLY_CHARS], True
    return text, False


def validate_decision(
    decision: Dict[str, Any],
    evidence_ids: Iterable[str],
    live_providers: Iterable[str],
    dependency_degraded: bool,
) -> Tuple[DecisionResult, List[str]]:
    """Validates node 07's structured output against what was actually supplied."""
    notices: List[str] = []
    provided_ids = set(evidence_ids)
    provided_sources = set(live_providers)

    reply = decision.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise GuardrailViolation("decision reply is empty")
    reply, truncated = sanitize_markdown(reply)
    if not reply:
        raise GuardrailViolation("decision reply contained no text after sanitization")
    if truncated:
        notices.append(f"reply was longer than {_MAX_REPLY_CHARS} characters and was shortened.")

    safety_level = decision.get("safety_level")
    if safety_level not in SAFETY_LEVELS:
        notices.append("safety_level was not recognised and was set to 'unknown'.")
        safety_level = "unknown"

    raw_ids = decision.get("used_evidence_ids") or []
    used_ids = [str(i) for i in raw_ids if str(i) in provided_ids] if isinstance(raw_ids, list) else []
    if isinstance(raw_ids, list) and len(used_ids) != len(raw_ids):
        notices.append("decision referenced evidence that was not supplied; those references were dropped.")

    raw_sources = decision.get("used_live_sources") or []
    used_sources = (
        [str(s) for s in raw_sources if str(s) in provided_sources] if isinstance(raw_sources, list) else []
    )
    if isinstance(raw_sources, list) and len(used_sources) != len(raw_sources):
        notices.append("decision referenced a live source that was not supplied; those references were dropped.")

    degraded = bool(decision.get("degraded", False)) or dependency_degraded

    raw_notices = decision.get("notices") or []
    decision_notices = [str(n) for n in raw_notices if str(n).strip()] if isinstance(raw_notices, list) else []

    result = DecisionResult(
        reply=reply,
        safety_level=safety_level,
        used_evidence_ids=used_ids,
        used_live_sources=used_sources,
        degraded=degraded,
        notices=decision_notices,
    )
    return result, notices
