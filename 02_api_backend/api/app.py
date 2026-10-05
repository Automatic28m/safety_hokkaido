"""FastAPI application factory.

Deliberately free of heavy imports (agent_core, faiss, sentence_transformers, ...)
so tests can build the app around a fake pipeline without loading any ML stack.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Callable, List, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .endpoints import create_router
from .schemas import ErrorResponse

logger = logging.getLogger("api_backend")

SAFE_VALIDATION_REPLY = (
    "ขออภัยค่ะ คำขอไม่ถูกต้อง กรุณาตรวจสอบข้อมูลแล้วลองใหม่อีกครั้ง / "
    "Sorry, the request was invalid. Please check it and try again."
)
SAFE_INTERNAL_REPLY = (
    "ขออภัยค่ะ เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่อีกครั้งในภายหลัง / "
    "Sorry, something went wrong on our side. Please try again later."
)

DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000"]


def _valid_uuid(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _parse_allowed_origins(raw: Optional[str]) -> List[str]:
    if not raw:
        return list(DEFAULT_ALLOWED_ORIGINS)
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    origins = [origin for origin in origins if origin != "*"]
    return origins or list(DEFAULT_ALLOWED_ORIGINS)


def _env_flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() == "true"


def create_app(
    get_pipeline: Callable[[], Any],
    reset_memory: Optional[Callable[[], None]] = None,
    allowed_origins: Optional[List[str]] = None,
    enable_debug_endpoints: Optional[bool] = None,
) -> FastAPI:
    if allowed_origins is None:
        allowed_origins = _parse_allowed_origins(os.getenv("ALLOWED_ORIGINS"))
    if enable_debug_endpoints is None:
        enable_debug_endpoints = _env_flag("ENABLE_DEBUG_ENDPOINTS")

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        incoming = request.headers.get("x-request-id")
        request_id = _valid_uuid(incoming) or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.route = None
        request.state.degraded = None

        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        outcome = "ok" if response.status_code < 400 else "error"
        logger.info(
            "request_id=%s method=%s path=%s http_status=%s outcome=%s route=%s degraded=%s latency_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            outcome,
            getattr(request.state, "route", None),
            getattr(request.state, "degraded", None),
            latency_ms,
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
        request.state.degraded = True
        errors = [
            {"loc": list(error.get("loc", [])), "msg": error.get("msg", "")}
            for error in exc.errors()
        ]
        body = ErrorResponse(reply=SAFE_VALIDATION_REPLY, request_id=request_id, detail=errors)
        return JSONResponse(status_code=400, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
        logger.exception("request_id=%s unhandled exception", request_id)
        request.state.degraded = True
        body = ErrorResponse(reply=SAFE_INTERNAL_REPLY, request_id=request_id, detail="internal_error")
        return JSONResponse(status_code=500, content=body.model_dump())

    router = create_router(
        get_pipeline=get_pipeline,
        reset_memory=reset_memory,
        enable_debug_endpoints=enable_debug_endpoints,
    )
    app.include_router(router)

    return app
