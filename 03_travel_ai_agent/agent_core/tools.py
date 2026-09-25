"""Tool registry for node 03.

Node 03 is the only module that selects and invokes node 04 adapters. Every
adapter is wrapped so that a failure becomes an explicit ``unavailable``
snapshot instead of an exception; the orchestration never guesses.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from agent_core.schemas import SNAPSHOT_STATUSES, TOOL_NAMES, ToolCall

logger = logging.getLogger("travel_ai_agent")

try:  # node 04 adapters; a broken or missing node 04 degrades tools instead of crashing node 03
    from external_data.tools import check_train_status, get_disaster_warnings, get_real_time_weather

    _ADAPTERS_AVAILABLE = True
except Exception as _import_error:  # pragma: no cover - exercised only when node 04 is absent/broken
    logger.error("node 04 adapters unavailable: %s", _import_error.__class__.__name__)
    get_real_time_weather = get_disaster_warnings = check_train_status = None  # type: ignore
    _ADAPTERS_AVAILABLE = False


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def unavailable_snapshot(tool: str, scope: str, error_code: str, notice: str) -> Dict[str, Any]:
    spec = TOOL_SPECS.get(tool, {})
    return {
        "provider": spec.get("provider", tool),
        "kind": spec.get("kind", tool),
        "scope": scope,
        "status": "unavailable",
        "fetched_at": _utc_now(),
        "expires_at": None,
        "data": None,
        "source_url": spec.get("source_url"),
        "error_code": error_code,
        "notice": notice,
    }


def snapshot_to_dict(snapshot: Any) -> Optional[Dict[str, Any]]:
    if snapshot is None:
        return None
    if hasattr(snapshot, "to_dict"):
        try:
            data = snapshot.to_dict()
        except Exception:  # pragma: no cover - defensive
            return None
    elif isinstance(snapshot, dict):
        data = dict(snapshot)
    else:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("status") not in SNAPSHOT_STATUSES:
        data["status"] = "unavailable"
        data.setdefault("error_code", "INVALID_STATUS")
    return data


TOOL_SPECS: Dict[str, Dict[str, Any]] = {
    "weather": {
        "adapter": get_real_time_weather,
        "arg": "city",
        "provider": "meteosource",
        "kind": "weather",
        "source_url": "https://www.meteosource.com",
    },
    "disaster": {
        "adapter": get_disaster_warnings,
        "arg": "region",
        "provider": "jma",
        "kind": "disaster",
        "source_url": "https://www.jma.go.jp/bosai/",
    },
    "train": {
        "adapter": check_train_status,
        "arg": "line_name",
        "provider": "jr_hokkaido_simulator",
        "kind": "train",
        "source_url": "https://www.jrhokkaido.co.jp/",
    },
}


class ToolExecutor:
    """Executes validated ``ToolCall`` objects against node 04 adapters."""

    def __init__(self, adapters: Optional[Dict[str, Callable[..., Any]]] = None):
        self.adapters: Dict[str, Optional[Callable[..., Any]]] = {
            name: TOOL_SPECS[name]["adapter"] for name in TOOL_NAMES
        }
        if adapters:
            for name, adapter in adapters.items():
                if name in self.adapters:
                    self.adapters[name] = adapter

    def allowed_tools(self) -> List[str]:
        return [name for name in TOOL_NAMES if self.adapters.get(name) is not None]

    @staticmethod
    def argument_name(tool: str) -> str:
        return TOOL_SPECS[tool]["arg"]

    def execute(self, call: ToolCall) -> Dict[str, Any]:
        adapter = self.adapters.get(call.name)
        arg_name = self.argument_name(call.name)
        scope = str(call.args.get(arg_name, ""))

        if adapter is None:
            return unavailable_snapshot(
                call.name, scope, "ADAPTER_MISSING", f"Adapter for '{call.name}' is not installed."
            )

        try:
            raw = adapter(scope)
        except Exception as exc:  # adapters should not raise, but never trust that
            logger.exception("tool '%s' raised", call.name)
            return unavailable_snapshot(
                call.name, scope, "ADAPTER_ERROR", f"Adapter '{call.name}' failed: {exc.__class__.__name__}."
            )

        snapshot = snapshot_to_dict(raw)
        if snapshot is None:
            return unavailable_snapshot(
                call.name, scope, "MALFORMED_SNAPSHOT", f"Adapter '{call.name}' returned an unreadable snapshot."
            )
        return snapshot
