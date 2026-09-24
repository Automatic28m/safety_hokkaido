"""Contract tests for the /ask HTTP layer.

These tests build the FastAPI app from api.app.create_app() around a fake
pipeline, so no Groq/FAISS/network calls ever happen here.
"""
import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.errors import PipelineUnavailableError


class FakePipeline:
    """Legacy pipeline: only has ask(), returns a plain string."""

    def __init__(self, reply="ok"):
        self.reply = reply
        self.calls = []

    def ask(self, query, chat_history=None, enabled_agents=None):
        self.calls.append(
            {"query": query, "chat_history": chat_history, "enabled_agents": enabled_agents}
        )
        return self.reply


class RaisingPipeline:
    def __init__(self, exc):
        self.exc = exc

    def ask(self, query, chat_history=None, enabled_agents=None):
        raise self.exc


class NonStringPipeline:
    def ask(self, query, chat_history=None, enabled_agents=None):
        return {"not": "a string"}


class StructuredPipeline:
    """New-style pipeline exposing ask_structured()."""

    def __init__(self, result):
        self.result = result
        self.calls = []

    def ask_structured(self, normalized):
        self.calls.append(normalized)
        return self.result


def make_app(pipeline, reset_memory=None, allowed_origins=None, enable_debug_endpoints=False):
    return create_app(
        get_pipeline=lambda: pipeline,
        reset_memory=reset_memory,
        allowed_origins=allowed_origins,
        enable_debug_endpoints=enable_debug_endpoints,
    )


def is_uuid(value):
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_legacy_message_mode():
    pipeline = FakePipeline(reply="hello")
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "Is it safe today?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "hello"
    assert body["status"] == "ok"
    assert body["degraded"] is False
    assert is_uuid(body["request_id"])
    assert len(pipeline.calls) == 1
    assert pipeline.calls[0]["query"] == "Is it safe today?"
    assert pipeline.calls[0]["chat_history"] is None
    assert pipeline.calls[0]["enabled_agents"] == {"weather": True, "disaster": True, "train": True}


def test_canonical_messages_mode_sends_full_history_to_ask():
    pipeline = FakePipeline(reply="hi there")
    client = TestClient(make_app(pipeline))

    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello, how can I help?"},
        {"role": "user", "content": "is it snowing in Sapporo?"},
    ]
    resp = client.post("/ask", json={"messages": messages})

    assert resp.status_code == 200
    assert resp.json()["reply"] == "hi there"
    assert len(pipeline.calls) == 1
    call = pipeline.calls[0]
    assert call["query"] == "is it snowing in Sapporo?"
    assert call["chat_history"] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello, how can I help?"},
        {"role": "user", "content": "is it snowing in Sapporo?"},
    ]


def test_role_ai_is_coerced_and_timestamp_is_dropped():
    pipeline = FakePipeline(reply="ok")
    client = TestClient(make_app(pipeline))

    messages = [
        {"role": "ai", "content": "Hi! I'm Tamago.", "timestamp": "10:00 AM"},
        {"role": "user", "content": "what about earthquakes?", "timestamp": "10:01 AM"},
    ]
    resp = client.post("/ask", json={"messages": messages})

    assert resp.status_code == 200
    call = pipeline.calls[0]
    assert call["chat_history"][0] == {"role": "assistant", "content": "Hi! I'm Tamago."}
    assert "timestamp" not in call["chat_history"][0]
    assert "timestamp" not in call["chat_history"][1]


def test_thai_query_with_surrounding_whitespace_is_forwarded_raw():
    pipeline = FakePipeline(reply="ตอบแล้วค่ะ")
    client = TestClient(make_app(pipeline))

    raw_query = "  แผ่นดินไหววันนี้อันตรายไหม  "
    resp = client.post("/ask", json={"message": raw_query})

    assert resp.status_code == 200
    assert pipeline.calls[0]["query"] == raw_query


def test_both_message_and_messages_prefers_messages():
    pipeline = FakePipeline(reply="ok")
    client = TestClient(make_app(pipeline))

    resp = client.post(
        "/ask",
        json={
            "message": "legacy text",
            "messages": [{"role": "user", "content": "canonical text"}],
        },
    )

    assert resp.status_code == 200
    assert pipeline.calls[0]["query"] == "canonical text"


# ---------------------------------------------------------------------------
# enabled_agents behavior
# ---------------------------------------------------------------------------


def test_enabled_agents_default_all_true():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))

    client.post("/ask", json={"message": "hi"})

    assert pipeline.calls[0]["enabled_agents"] == {"weather": True, "disaster": True, "train": True}


def test_enabled_agents_missing_key_defaults_true_like_chatbot_jsx():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))

    client.post(
        "/ask",
        json={"message": "hi", "enabled_agents": {"weather": True, "disaster": True}},
    )

    assert pipeline.calls[0]["enabled_agents"] == {"weather": True, "disaster": True, "train": True}


def test_enabled_agents_unknown_key_is_ignored():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))

    client.post(
        "/ask",
        json={"message": "hi", "enabled_agents": {"weather": False, "made_up_tool": True}},
    )

    result = pipeline.calls[0]["enabled_agents"]
    assert result == {"weather": False, "disaster": True, "train": True}
    assert "made_up_tool" not in result


def test_enabled_agents_dict_not_shared_across_requests():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))

    client.post("/ask", json={"message": "hi", "enabled_agents": {"weather": False}})
    client.post("/ask", json={"message": "hi again"})

    first = pipeline.calls[0]["enabled_agents"]
    second = pipeline.calls[1]["enabled_agents"]
    assert first == {"weather": False, "disaster": True, "train": True}
    assert second == {"weather": True, "disaster": True, "train": True}
    assert first is not second


# ---------------------------------------------------------------------------
# 400s
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"messages": []},
        {"messages": [{"role": "assistant", "content": "not a user turn"}]},
        {"messages": [{"role": "bogus", "content": "hi"}]},
        {"messages": [{"content": "missing role"}]},
        {"messages": [{"role": "user"}]},
        {"messages": [{"role": "user", "content": "x" * 4001}]},
        {"messages": [{"role": "user", "content": "hi"}] * 51},
        {"message": "hi", "enabled_agents": "not-a-dict"},
        {"message": "hi", "enabled_agents": {"weather": "not-a-bool"}},
    ],
)
def test_invalid_requests_return_400(payload):
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json=payload)

    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "error"
    assert body["degraded"] is True
    assert body["reply"]
    assert is_uuid(body["request_id"])


def test_malformed_json_returns_400_without_reflecting_input():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))

    resp = client.post(
        "/ask",
        content=b"{not valid json sk-secret-token",
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400
    assert "sk-secret-token" not in resp.text


def test_400_does_not_reflect_user_input():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"messages": [{"role": "user", "content": "top-secret-value"}] * 51})

    assert resp.status_code == 400
    assert "top-secret-value" not in resp.text


# ---------------------------------------------------------------------------
# 503s
# ---------------------------------------------------------------------------


def test_pipeline_none_returns_503():
    client = TestClient(make_app(None))

    resp = client.post("/ask", json={"message": "hi"})

    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "error"
    assert body["degraded"] is True
    assert body["reply"]
    assert is_uuid(body["request_id"])


def test_pipeline_unavailable_error_returns_503():
    pipeline = RaisingPipeline(PipelineUnavailableError("down for maintenance"))
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"})

    assert resp.status_code == 503
    assert resp.json()["reply"]


def test_ask_structured_unavailable_status_returns_503_with_notices():
    pipeline = StructuredPipeline(
        {"status": "unavailable", "reply": "n/a", "notices": ["groq_down", "retrying"]}
    )
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"})

    assert resp.status_code == 503
    body = resp.json()
    assert body["notices"] == ["groq_down", "retrying"]
    assert body["reply"]


# ---------------------------------------------------------------------------
# 500s
# ---------------------------------------------------------------------------


def test_exception_with_secret_does_not_leak_into_response():
    pipeline = RaisingPipeline(RuntimeError("leaked sk-secret-abc123"))
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"})

    assert resp.status_code == 500
    assert "sk-secret-abc123" not in resp.text
    body = resp.json()
    assert body["status"] == "error"
    assert body["degraded"] is True
    assert body["reply"]


def test_non_string_reply_returns_500():
    pipeline = NonStringPipeline()
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"})

    assert resp.status_code == 500
    body = resp.json()
    assert body["reply"]
    assert body["status"] == "error"
    assert body["degraded"] is True


# ---------------------------------------------------------------------------
# ask_structured field mapping
# ---------------------------------------------------------------------------


def test_ask_structured_fields_are_forwarded():
    pipeline = StructuredPipeline(
        {
            "reply": "here is the forecast",
            "status": "ok",
            "route": "rag+realtime",
            "degraded": False,
            "notices": ["used_cache"],
            "evidence": [{"source": "doc1"}],
            "live_sources": [{"tool": "weather"}],
        }
    )
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "here is the forecast"
    assert body["route"] == "rag+realtime"
    assert body["notices"] == ["used_cache"]
    assert body["evidence"] == [{"source": "doc1"}]
    assert body["live_sources"] == [{"tool": "weather"}]


def test_ask_structured_unknown_route_becomes_none():
    pipeline = StructuredPipeline({"reply": "ok", "status": "ok", "route": "not-a-real-route"})
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"})

    assert resp.status_code == 200
    assert resp.json()["route"] is None


def test_ask_structured_malformed_evidence_is_dropped():
    pipeline = StructuredPipeline({"reply": "ok", "status": "ok", "evidence": "not-a-list"})
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"})

    assert resp.status_code == 200
    assert resp.json()["evidence"] == []


def test_node03_receives_same_request_id_as_response():
    pipeline = StructuredPipeline({"reply": "ok", "status": "ok"})
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"})

    body = resp.json()
    assert pipeline.calls[0]["request_id"] == body["request_id"]


# ---------------------------------------------------------------------------
# Request ID propagation
# ---------------------------------------------------------------------------


def test_valid_incoming_request_id_is_reused():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))
    incoming_id = str(uuid.uuid4())

    resp = client.post("/ask", json={"message": "hi"}, headers={"X-Request-ID": incoming_id})

    assert resp.headers["X-Request-ID"] == incoming_id
    assert resp.json()["request_id"] == incoming_id


def test_invalid_incoming_request_id_is_replaced():
    pipeline = FakePipeline()
    client = TestClient(make_app(pipeline))

    resp = client.post("/ask", json={"message": "hi"}, headers={"X-Request-ID": "not-a-uuid"})

    header_id = resp.headers["X-Request-ID"]
    assert is_uuid(header_id)
    assert header_id != "not-a-uuid"
    assert resp.json()["request_id"] == header_id


# ---------------------------------------------------------------------------
# /health, GET /, CORS
# ---------------------------------------------------------------------------


def test_health_ok_when_pipeline_ready():
    client = TestClient(make_app(FakePipeline()))
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_503_when_pipeline_not_ready():
    client = TestClient(make_app(None))
    resp = client.get("/health")
    assert resp.status_code == 503


def test_root_status():
    client = TestClient(make_app(FakePipeline()))
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "RAG Backend is running"}


def test_cors_allowed_origin_is_echoed():
    client = TestClient(make_app(FakePipeline(), allowed_origins=["http://localhost:3000"]))

    resp = client.options(
        "/ask",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "access-control-allow-credentials" not in resp.headers


def test_cors_disallowed_origin_is_not_echoed():
    client = TestClient(make_app(FakePipeline(), allowed_origins=["http://localhost:3000"]))

    resp = client.options(
        "/ask",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert resp.headers.get("access-control-allow-origin") != "http://evil.example"


def test_wildcard_origin_is_stripped_from_env(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    from api.app import _parse_allowed_origins

    assert "*" not in _parse_allowed_origins("*")
    assert _parse_allowed_origins("*") == ["http://localhost:3000"]


# ---------------------------------------------------------------------------
# /reset_memory
# ---------------------------------------------------------------------------


def test_reset_memory_404_by_default():
    called = {"value": False}

    def reset():
        called["value"] = True

    client = TestClient(make_app(FakePipeline(), reset_memory=reset, enable_debug_endpoints=False))

    resp = client.post("/reset_memory")

    assert resp.status_code == 404
    assert called["value"] is False


def test_reset_memory_200_when_debug_enabled():
    called = {"value": False}

    def reset():
        called["value"] = True

    client = TestClient(make_app(FakePipeline(), reset_memory=reset, enable_debug_endpoints=True))

    resp = client.post("/reset_memory")

    assert resp.status_code == 200
    assert called["value"] is True


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def test_logs_have_latency_and_no_user_content(caplog):
    pipeline = FakePipeline(reply="a secret-looking reply")
    client = TestClient(make_app(pipeline))

    with caplog.at_level(logging.INFO, logger="api_backend"):
        client.post("/ask", json={"message": "a very private question"})

    messages = [record.getMessage() for record in caplog.records]
    assert any("latency_ms=" in m for m in messages)
    assert not any("a very private question" in m for m in messages)
    assert not any("a secret-looking reply" in m for m in messages)
