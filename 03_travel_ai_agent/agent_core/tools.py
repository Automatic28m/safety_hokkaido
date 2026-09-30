"""Tool registry for node 03.

Node 03 is the only module that selects and invokes node 04 adapters. Every
adapter is wrapped so that a failure becomes an explicit ``unavailable``
snapshot instead of an exception; the orchestration never guesses.

Contract expected from node 04: each adapter takes one primitive argument and
returns a ``LiveDataSnapshot`` (or an equivalent dict) with ``provider``,
``kind``, ``scope``, ``status`` (ok | partial | stale | unavailable | mocked),
``fetched_at``, ``expires_at``, ``data``, ``source_url``, ``error_code``.
Anything else is reported as an integration incompatibility, never repaired here.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from agent_core.schemas import SNAPSHOT_STATUSES, TOOL_NAMES, ToolCall

logger = logging.getLogger("travel_ai_agent")

ADAPTER_IMPORT_ERROR: Optional[str] = None
try:  # node 04 adapters; a broken or missing node 04 degrades tools instead of crashing node 03
    from external_data.tools import check_train_status, get_disaster_warnings, get_real_time_weather
except Exception as _import_error:  # node 04 absent or failing to import
    ADAPTER_IMPORT_ERROR = f"{_import_error.__class__.__name__}: {_import_error}"[:200]
    logger.error("node 04 adapters could not be imported: %s", ADAPTER_IMPORT_ERROR)
    get_real_time_weather = get_disaster_warnings = check_train_status = None  # type: ignore


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
    """Reads a node 04 snapshot. Returns ``None`` when it does not follow the contract."""
    if snapshot is None or isinstance(snapshot, str):
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

    def __init__(self, adapters: Optional[Dict[str, Optional[Callable[..., Any]]]] = None):
        self.adapters: Dict[str, Optional[Callable[..., Any]]] = {
            name: TOOL_SPECS[name]["adapter"] for name in TOOL_NAMES
        }
        injected = set()
        if adapters:
            for name, adapter in adapters.items():
                if name in self.adapters:
                    self.adapters[name] = adapter
                    injected.add(name)
        self._unavailable_reasons: Dict[str, str] = {}
        for name in TOOL_NAMES:
            if self.adapters[name] is None:
                if ADAPTER_IMPORT_ERROR and name not in injected:
                    self._unavailable_reasons[name] = f"node 04 adapters could not be imported ({ADAPTER_IMPORT_ERROR})"
                else:
                    self._unavailable_reasons[name] = "adapter is not installed in this deployment"

    def allowed_tools(self) -> List[str]:
        return [name for name in TOOL_NAMES if self.adapters.get(name) is not None]

    def unavailable_reason(self, tool: str) -> str:
        return self._unavailable_reasons.get(tool, "adapter is not available")

    @staticmethod
    def argument_name(tool: str) -> str:
        return TOOL_SPECS[tool]["arg"]

    def execute(self, call: ToolCall) -> Dict[str, Any]:
        adapter = self.adapters.get(call.name)
        arg_name = self.argument_name(call.name)
        scope = str(call.args.get(arg_name, ""))

        if adapter is None:
            return unavailable_snapshot(call.name, scope, "ADAPTER_MISSING", self.unavailable_reason(call.name))

        try:
            raw = adapter(scope)
        except Exception as exc:  # adapters should not raise, but never trust that
            logger.exception("tool '%s' raised", call.name)
            return unavailable_snapshot(
                call.name, scope, "ADAPTER_ERROR", f"Adapter '{call.name}' failed: {exc.__class__.__name__}."
            )

        if isinstance(raw, str):
            return unavailable_snapshot(
                call.name,
                scope,
                "INCOMPATIBLE_ADAPTER_OUTPUT",
                f"Adapter '{call.name}' returned plain text instead of a LiveDataSnapshot; "
                "the result was not used (node 04 contract).",
            )

        snapshot = snapshot_to_dict(raw)
        if snapshot is None:
            return unavailable_snapshot(
                call.name, scope, "MALFORMED_SNAPSHOT", f"Adapter '{call.name}' returned an unreadable snapshot."
            )
        return snapshot
