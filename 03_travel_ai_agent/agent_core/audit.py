"""Audit event emission to node 08.

Node 03 sends one privacy-minimized trace per answer. The event contains no
query text, reply text or user identifier. Emission never raises and never
changes the answer.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Optional

import requests

from agent_core.schemas import AuditEvent, ToolResult, utc_now_iso

logger = logging.getLogger("travel_ai_agent")

AUDIT_URL_ENV = "NODE08_AUDIT_URL"
AUDIT_TOKEN_ENV = "NODE08_AUDIT_TOKEN"
DEFAULT_TIMEOUT_SECONDS = 3.0


def build_audit_event(
    request_id: str,
    route: str,
    degraded: bool,
    evidence: List[Dict[str, Any]],
    live_results: List[ToolResult],
    index_version: Optional[str],
) -> AuditEvent:
    evidence_ids = [str(e["chunk_id"]) for e in evidence if e.get("chunk_id")]
    versions: List[str] = []
    for item in evidence:
        version = (item.get("metadata") or {}).get("source_version")
        if version and str(version) not in versions:
            versions.append(str(version))
    for result in live_results:
        marker = f"{result.provider}@{result.snapshot.get('fetched_at') or 'unknown'}"
        if marker not in versions:
            versions.append(marker)
    return AuditEvent(
        request_id=request_id,
        timestamp=utc_now_iso(),
        route=route,
        degraded=degraded,
        evidence_ids=evidence_ids[:100],
        source_versions=[v[:256] for v in versions][:100],
        index_version=(index_version or None),
    )


class AuditEmitter:
    """Sends events to node 08 over HTTP when configured, otherwise logs them."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        sink: Optional[Callable[[Dict[str, Any]], Any]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        session: Optional[Any] = None,
    ):
        self.url = url if url is not None else os.environ.get(AUDIT_URL_ENV, "")
        self.token = token if token is not None else os.environ.get(AUDIT_TOKEN_ENV, "")
        self.sink = sink
        self.timeout = timeout
        self._session = session or requests

    def emit(self, event: AuditEvent) -> bool:
        payload = event.to_payload()
        try:
            if self.sink is not None:
                self.sink(payload)
                return True
            if self.url and self.token:
                response = self._session.post(
                    self.url,
                    json=payload,
                    headers={"X-Node08-Token": self.token},
                    timeout=self.timeout,
                )
                if getattr(response, "status_code", 0) not in (200, 201):
                    logger.warning("audit event rejected by node 08: HTTP %s", getattr(response, "status_code", "?"))
                    return False
                return True
            logger.info(
                "audit request_id=%s route=%s degraded=%s evidence=%d",
                event.request_id, event.route, event.degraded, len(event.evidence_ids),
            )
            return True
        except Exception as exc:
            logger.warning("audit event emission failed: %s", exc.__class__.__name__)
            return False
