"""FastAPI routes: HTTP-only concerns. No orchestration/retrieval/LLM decisions here."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .errors import PipelineUnavailableError
from .schemas import ROUTES, AskResponse, ChatRequest, ErrorResponse, NormalizedAskRequest

logger = logging.getLogger("api_backend")

SAFE_UNAVAILABLE_REPLY = (
    "ขออภัยค่ะ ระบบผู้ช่วยยังไม่พร้อมใช้งานในขณะนี้ กรุณาลองใหม่อีกครั้งในภายหลัง / "
    "Sorry, the assistant is not available right now. Please try again later."
)
SAFE_ERROR_REPLY = (
    "ขออภัยค่ะ เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่อีกครั้งในภายหลัง / "
    "Sorry, something went wrong on our side. Please try again later."
)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or "unknown"


def _mark_state(request: Request, route: Optional[str], degraded: bool) -> None:
    request.state.route = route
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
    def ask(payload: ChatRequest, request: Request):
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

                route = raw.get("route")
                if route not in ROUTES:
                    route = None

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
                status, route, degraded, notices, evidence, live_sources = (
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

        _mark_state(request, route, degraded)
        response_body = AskResponse(
            reply=reply,
            request_id=request_id,
            status=status,
            route=route,
            degraded=degraded,
            notices=notices,
            evidence=evidence,
            live_sources=live_sources,
        )
        return response_body.model_dump()

    @router.post("/reset_memory")
    def reset_memory_endpoint():
        if not enable_debug_endpoints or reset_memory is None:
            raise HTTPException(status_code=404)
        reset_memory()
        return {"status": "Memory wiped."}

    return router
