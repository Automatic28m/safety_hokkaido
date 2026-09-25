"""Optional standalone HTTP interface for node 08.

Run from this directory: uvicorn app:app --host 127.0.0.1 --port 8008
The audit endpoint is internal and requires NODE08_AUDIT_TOKEN.
"""

import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from service import AuditStore, ValidationError

app = FastAPI(title="Safety Hokkaido feedback", docs_url=None, redoc_url=None)
store = AuditStore(Path(os.environ.get("NODE08_DB_PATH", Path(__file__).parent / "feedback.sqlite3")))


@app.exception_handler(ValidationError)
async def invalid_input(_request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/audit", status_code=201)
def record_audit(payload: dict, x_node08_token: str | None = Header(default=None)):
    token = os.environ.get("NODE08_AUDIT_TOKEN")
    if not token or x_node08_token != token:
        raise HTTPException(status_code=403, detail="audit access denied")
    try:
        item = store.record_audit(payload)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="request_id already recorded")
    return {"request_id": item["request_id"], "status": "recorded"}


@app.post("/feedback", status_code=201)
def record_feedback(payload: dict):
    item = store.record_feedback(payload)
    return {"request_id": item["request_id"], "status": "recorded"}
