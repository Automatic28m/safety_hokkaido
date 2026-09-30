from agent_core.audit import AuditEmitter, build_audit_event
from agent_core.schemas import ToolCall, ToolResult
from agent_core.tools import ToolExecutor, snapshot_to_dict


class Snapshot:
    def __init__(self, status):
        self.status = status

    def to_dict(self):
        return {"provider": "p", "kind": "k", "scope": "s", "status": self.status, "fetched_at": "t"}


def test_executor_normalizes_snapshot_objects_and_invalid_status():
    executor = ToolExecutor(adapters={"weather": lambda city: Snapshot("ok"), "train": lambda l: Snapshot("weird")})
    assert executor.execute(ToolCall(name="weather", args={"city": "Sapporo"}))["status"] == "ok"
    weird = executor.execute(ToolCall(name="train", args={"line_name": "All"}))
    assert weird["status"] == "unavailable" and weird["error_code"] == "INVALID_STATUS"
    assert snapshot_to_dict("not a snapshot") is None


def test_executor_missing_adapter_and_malformed_return():
    executor = ToolExecutor(adapters={"weather": None, "disaster": lambda r: 42})
    missing = executor.execute(ToolCall(name="weather", args={"city": "Sapporo"}))
    assert missing["status"] == "unavailable" and missing["error_code"] == "ADAPTER_MISSING"
    malformed = executor.execute(ToolCall(name="disaster", args={"region": "Hokkaido"}))
    assert malformed["error_code"] == "MALFORMED_SNAPSHOT"
    assert "weather" not in executor.allowed_tools()


def test_build_audit_event_contains_no_text_and_tracks_versions():
    evidence = [
        {"chunk_id": "c1", "text": "private", "metadata": {"source_version": "v1"}},
        {"chunk_id": "c2", "text": "private", "metadata": {"source_version": "v1"}},
    ]
    live = [ToolResult(call=ToolCall(name="weather", args={"city": "Sapporo"}),
                       snapshot={"provider": "meteosource", "status": "ok", "fetched_at": "2026-09-26T00:00:00Z"})]
    event = build_audit_event("rid", "rag+realtime", False, evidence, live, "idx-1")
    payload = event.to_payload()
    assert payload["evidence_ids"] == ["c1", "c2"]
    assert payload["source_versions"] == ["v1", "meteosource@2026-09-26T00:00:00Z"]
    assert payload["index_version"] == "idx-1" and payload["evaluation_schema_version"] == "1"
    assert "private" not in str(payload)


def test_emitter_uses_sink_http_or_log_and_never_raises():
    captured = []
    event = build_audit_event("rid", "rag", True, [], [], None)
    assert AuditEmitter(sink=captured.append).emit(event) is True and captured[0]["route"] == "rag"

    class Response:
        status_code = 201

    class Session:
        def __init__(self):
            self.posts = []

        def post(self, url, json=None, headers=None, timeout=None):
            self.posts.append((url, json, headers))
            return Response()

    session = Session()
    assert AuditEmitter(url="http://node08/audit", token="t", session=session).emit(event) is True
    assert session.posts[0][2] == {"X-Node08-Token": "t"} and "index_version" not in session.posts[0][1]

    def failing(_):
        raise RuntimeError("sink down")

    assert AuditEmitter(sink=failing).emit(event) is False
    assert AuditEmitter(url="", token="").emit(event) is True
