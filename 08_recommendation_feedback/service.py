"""Privacy-minimized audit and feedback storage for node 08.

This module has no dependency on the answer-generation runtime. Callers pass
JSON-compatible dictionaries only; query text and user identifiers are rejected.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

ROUTES = {"general", "rag", "realtime", "rag+realtime"}
AUDIT_FIELDS = {
    "request_id", "timestamp", "route", "degraded", "evidence_ids",
    "source_versions", "evaluation_schema_version", "index_version",
}
FEEDBACK_FIELDS = {"request_id", "rating"}


class ValidationError(ValueError):
    pass


def _uuid(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError("request_id must be a UUID string")
    try:
        return str(UUID(value))
    except (ValueError, AttributeError) as exc:
        raise ValidationError("request_id must be a UUID string") from exc


def _timestamp(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError("timestamp must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("timestamp must be an ISO-8601 string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or len(value) > 100:
        raise ValidationError(f"{name} must be an array of at most 100 strings")
    if any(not isinstance(item, str) or not item or len(item) > 256 for item in value):
        raise ValidationError(f"{name} contains an invalid string")
    return value


def validate_audit(event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(event, dict) or set(event) - AUDIT_FIELDS:
        raise ValidationError("audit contains unsupported fields")
    required = AUDIT_FIELDS - {"index_version"}
    if not required <= set(event):
        raise ValidationError(f"audit missing fields: {', '.join(sorted(required - set(event)))}")
    route = event["route"]
    if not isinstance(route, str) or route not in ROUTES:
        raise ValidationError("route is invalid")
    if type(event["degraded"]) is not bool:
        raise ValidationError("degraded must be boolean")
    if event["evaluation_schema_version"] != "1":
        raise ValidationError("unsupported evaluation_schema_version")
    index_version = event.get("index_version")
    if index_version is not None and (not isinstance(index_version, str) or not 0 < len(index_version) <= 256):
        raise ValidationError("index_version is invalid")
    return {
        "request_id": _uuid(event["request_id"]),
        "timestamp": _timestamp(event["timestamp"]),
        "route": route,
        "degraded": event["degraded"],
        "evidence_ids": _string_list(event["evidence_ids"], "evidence_ids"),
        "source_versions": _string_list(event["source_versions"], "source_versions"),
        "evaluation_schema_version": "1",
        "index_version": index_version,
    }


def validate_feedback(signal: dict[str, Any]) -> dict[str, str]:
    if not isinstance(signal, dict) or set(signal) != FEEDBACK_FIELDS:
        raise ValidationError("feedback must contain only request_id and rating")
    if signal["rating"] not in ("up", "down"):
        raise ValidationError("rating must be up or down")
    return {"request_id": _uuid(signal["request_id"]), "rating": signal["rating"]}


class AuditStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS audit (
                    request_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    route TEXT NOT NULL,
                    degraded INTEGER NOT NULL,
                    evidence_ids TEXT NOT NULL,
                    source_versions TEXT NOT NULL,
                    evaluation_schema_version TEXT NOT NULL,
                    index_version TEXT
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    request_id TEXT PRIMARY KEY REFERENCES audit(request_id) ON DELETE CASCADE,
                    rating TEXT NOT NULL CHECK (rating IN ('up', 'down')),
                    created_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys = ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def record_audit(self, event: dict[str, Any]) -> dict[str, Any]:
        item = validate_audit(event)
        with self._connect() as db:
            db.execute(
                "INSERT INTO audit VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (item["request_id"], item["timestamp"], item["route"], int(item["degraded"]),
                 json.dumps(item["evidence_ids"]), json.dumps(item["source_versions"]),
                 item["evaluation_schema_version"], item["index_version"]),
            )
        return item

    def record_feedback(self, signal: dict[str, Any]) -> dict[str, str]:
        item = validate_feedback(signal)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connect() as db:
            if db.execute("SELECT 1 FROM audit WHERE request_id = ?", (item["request_id"],)).fetchone() is None:
                raise ValidationError("unknown request_id")
            db.execute(
                "INSERT INTO feedback VALUES (?, ?, ?) "
                "ON CONFLICT(request_id) DO UPDATE SET rating = excluded.rating, created_at = excluded.created_at",
                (item["request_id"], item["rating"], now),
            )
        return item

    def get_audit(self, request_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM audit WHERE request_id = ?", (_uuid(request_id),)).fetchone()
        if row is None:
            return None
        return dict(zip(
            ("request_id", "timestamp", "route", "degraded", "evidence_ids",
             "source_versions", "evaluation_schema_version", "index_version"),
            (row[0], row[1], row[2], bool(row[3]), json.loads(row[4]), json.loads(row[5]), row[6], row[7]),
        ))

    def prune(self, retention_days: int = 30) -> int:
        if not isinstance(retention_days, int) or retention_days < 1:
            raise ValidationError("retention_days must be a positive integer")
        cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat().replace("+00:00", "Z")
        with self._connect() as db:
            cursor = db.execute("DELETE FROM audit WHERE timestamp < ?", (cutoff,))
            return cursor.rowcount
