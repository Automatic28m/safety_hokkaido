"""FastAPI routes: HTTP-only concerns. No orchestration/retrieval/LLM decisions here."""
from __future__ import annotations

import logging
import os
import requests
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .errors import PipelineUnavailableError
from .schemas import AskResponse, ChatRequest, ErrorResponse, NormalizedAskRequest, RouteIntent, FeedbackRequest

logger = logging.getLogger("api_backend")

SAFE_UNAVAILABLE_REPLY = (
    "ขออภัยค่ะ ระบบผู้ช่วยยังไม่พร้อมใช้งานในขณะนี้ กรุณาลองใหม่อีกครั้งในภายหลัง / "
    "Sorry, the assistant is not available right now. Please try again later."
)
SAFE_ERROR_REPLY = (
    "ขออภัยค่ะ เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่อีกครั้งในภายหลัง / "
    "Sorry, something went wrong on our side. Please try again later."
)

def _send_audit_background(payload: dict) -> None:
    audit_url = os.environ.get("NODE08_AUDIT_URL", "http://127.0.0.1:8008/audit")
    audit_token = os.environ.get("NODE08_AUDIT_TOKEN", "")
    try:
        res = requests.post(
            audit_url,
            json=payload,
            headers={"X-Node08-Token": audit_token},
            timeout=2.0
        )
        if res.status_code >= 400:
            logger.warning(f"Audit rejected: {res.text}")
    except Exception as e:
        logger.warning("Failed to send audit log to module 08: %s", str(e))

def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or "unknown"


def _mark_state(request: Request, route_intent: Optional[RouteIntent], degraded: bool) -> None:
    # Store presence only, never the origin/destination text, so logs stay content-free.
    request.state.route = route_intent is not None
    request.state.degraded = degraded


def _unavailable_response(request: Request, request_id: str, notices: Optional[list] = None) -> JSONResponse:
    _mark_state(request, None, True)
    body = ErrorResponse(
        reply=SAFE_UNAVAILABLE_REPLY,
        request_id=request_id,
        detail="pipeline_unavailable",
        notices=notices or [],
    )
    return JSONResponse(status_code=503, content=body.model_dump())


def _internal_error_response(request: Request, request_id: str, detail: str) -> JSONResponse:
    _mark_state(request, None, True)
    body = ErrorResponse(reply=SAFE_ERROR_REPLY, request_id=request_id, detail=detail)
    return JSONResponse(status_code=500, content=body.model_dump())


def _messages_to_history(payload: ChatRequest) -> list:
    return [{"role": m.role.value, "content": m.content} for m in payload.messages]


def create_router(
    get_pipeline: Callable[[], Any],
    reset_memory: Optional[Callable[[], None]] = None,
    enable_debug_endpoints: bool = False,
) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    def read_root():
        return {"status": "RAG Backend is running"}

    @router.get("/health")
    def health():
        if get_pipeline() is None:
            raise HTTPException(status_code=503, detail="Pipeline is not initialized")
        return {"status": "ok"}

    @router.post("/ask")
    def ask(payload: ChatRequest, request: Request, background_tasks: BackgroundTasks):
        request_id = _request_id(request)
        pipeline = get_pipeline()

        if payload.message and payload.messages:
            logger.info(
                "request_id=%s both 'message' and 'messages' provided; using 'messages'",
                request_id,
            )

        if pipeline is None:
            return _unavailable_response(request, request_id)

        enabled_agents = payload.build_enabled_agents()
        input_mode = payload.input_mode

        if input_mode == "messages":
            chat_history = _messages_to_history(payload)
            original_query = payload.messages[-1].content
        else:
            chat_history = []
            original_query = payload.message

        normalized = NormalizedAskRequest(
            request_id=request_id,
            original_query=original_query,
            chat_history=chat_history,
            enabled_agents=enabled_agents,
            received_at=datetime.now(timezone.utc).isoformat(),
            input_mode=input_mode,
        )

        try:
            if hasattr(pipeline, "ask_structured"):
                raw = pipeline.ask_structured(normalized.model_dump())

                status = raw.get("status", "ok")
                if status == "unavailable":
                    return _unavailable_response(request, request_id, notices=raw.get("notices") or [])

                reply = raw.get("reply")

                raw_route_intent = raw.get("route_intent")
                route_intent = None
                if raw_route_intent is not None:
                    try:
                        route_intent = RouteIntent.model_validate(raw_route_intent, strict=True)
                    except ValidationError:
                        logger.warning("request_id=%s dropping malformed 'route_intent'", request_id)
                        route_intent = None

                raw_ui_widget = raw.get("ui_widget")
                ui_widget = None
                if raw_ui_widget is not None:
                    try:
                        from .schemas import UIWidget
                        ui_widget = UIWidget.model_validate(raw_ui_widget, strict=False)
                    except ValidationError:
                        logger.warning("request_id=%s dropping malformed 'ui_widget'", request_id)
                        ui_widget = None

                degraded = bool(raw.get("degraded", False))
                notices = raw.get("notices") or []

                evidence = raw.get("evidence")
                if not (isinstance(evidence, list) and all(isinstance(e, dict) for e in evidence)):
                    if evidence not in (None, []):
                        logger.warning("request_id=%s dropping malformed 'evidence'", request_id)
                    evidence = []

                live_sources = raw.get("live_sources")
                if not (isinstance(live_sources, list) and all(isinstance(s, dict) for s in live_sources)):
                    if live_sources not in (None, []):
                        logger.warning("request_id=%s dropping malformed 'live_sources'", request_id)
                    live_sources = []
            else:
                if input_mode == "messages":
                    reply = pipeline.ask(
                        original_query, chat_history=chat_history, enabled_agents=enabled_agents
                    )
                else:
                    reply = pipeline.ask(original_query, enabled_agents=enabled_agents)
                status, route_intent, degraded, notices, evidence, live_sources = (
                    "ok",
                    None,
                    False,
                    [],
                    [],
                    [],
                )
        except PipelineUnavailableError:
            return _unavailable_response(request, request_id)
        except Exception:
            logger.exception("request_id=%s unhandled error while asking pipeline", request_id)
            return _internal_error_response(request, request_id, "internal_error")

        if not isinstance(reply, str):
            logger.error("request_id=%s pipeline returned a non-string reply", request_id)
            return _internal_error_response(request, request_id, "invalid_reply_type")

        _mark_state(request, route_intent, degraded)
        response_body = AskResponse(
            reply=reply,
            request_id=request_id,
            status=status,
            route_intent=route_intent,
            ui_widget=ui_widget,
            degraded=degraded,
            notices=notices,
            evidence=evidence,
            live_sources=live_sources,
            used_model=raw.get("used_model") if hasattr(pipeline, "ask_structured") else None,
        )

        def extract_chunk_id(e):
            if not isinstance(e, dict):
                return str(e)[:255]
            if "chunk_id" in e:
                return e["chunk_id"]
            if "chunk" in e and isinstance(e["chunk"], dict) and "chunk_id" in e["chunk"]:
                return e["chunk"]["chunk_id"]
            return str(e)[:255]

        audit_payload = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "route": "rag",
            "degraded": degraded,
            "evidence_ids": [extract_chunk_id(e) for e in evidence] if evidence else [],
            "source_versions": ["corpus-2026-09-24"],
            "evaluation_schema_version": "1"
        }
        background_tasks.add_task(_send_audit_background, audit_payload)

        return response_body.model_dump()

    @router.post("/reset_memory")
    def reset_memory_endpoint():
        if not enable_debug_endpoints or reset_memory is None:
            raise HTTPException(status_code=404)
        reset_memory()
        return {"status": "Memory wiped."}

    @router.post("/feedback")
    def feedback_endpoint(payload: FeedbackRequest):
        feedback_url = os.environ.get("NODE08_FEEDBACK_URL", "http://127.0.0.1:8008/feedback")
        target_payload = {
            "request_id": payload.message_id,  # map frontend message_id to backend request_id
            "rating": payload.rating
        }
        try:
            res = requests.post(feedback_url, json=target_payload, timeout=2.0)
            res.raise_for_status()
            return {"status": "ok"}
        except requests.RequestException as e:
            logger.warning("Failed to send feedback to module 08: %s", str(e))
            raise HTTPException(status_code=503, detail="feedback_unavailable")

    return router
