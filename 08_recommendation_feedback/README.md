# Node 08: recommendation feedback

This folder contains a standalone, privacy-minimized audit and feedback service. It never changes a safety decision, prompt, model, or guardrail. No raw query, reply text, user ID, free-text feedback, or IP address is stored by the application.

## Audit contract

After a successful answer, node 03/07 should send one event to `POST /audit` with header `X-Node08-Token`. Example:

```json
{
  "request_id": "9a937e0e-8de4-48b1-881e-5cc0d2181418",
  "timestamp": "2026-09-25T10:00:00Z",
  "route": "rag",
  "degraded": false,
  "evidence_ids": ["jnto_earthquake_advices.json_0_part_0"],
  "source_versions": ["corpus-2026-09-24"],
  "evaluation_schema_version": "1",
  "index_version": "optional-index-version"
}
```

`index_version` is optional. All other fields are required. Unknown fields are rejected to prevent accidental collection of personal information. Repeated request IDs return `409`; the caller should generate one UUID per answer. Storage uses SQLite and enforces one feedback signal per request ID.

Node 01 may send `POST /feedback` with `{"request_id":"...","rating":"up"}` or `"down"`. The request ID must already exist in the audit store. Feedback can be changed by sending another signal for the same request ID. The application does not record request bodies in logs.

## Run

Install FastAPI and Uvicorn from the existing backend requirements, then run from this directory:

```powershell
$env:NODE08_AUDIT_TOKEN = '<random private token>'
$env:NODE08_DB_PATH = 'D:\path\to\private\feedback.sqlite3'
uvicorn app:app --host 127.0.0.1 --port 8008
python -m unittest test_node08.py
```

The service binds to localhost in this example. If deployed behind a proxy, restrict `/audit` to trusted callers and apply rate limiting to `/feedback`. Run `AuditStore(path).prune(retention_days=30)` on a scheduled job after the team approves a retention period; deletion cascades to feedback. Back up and restrict access to the SQLite database according to the deployment policy.

## Evaluation gate

`evaluate.py` accepts a JSON array of predictions with `question`, `retrieved_chunk_ids`, and `judge_scores` (`faithfulness` and `relevance`, each 1–10). It compares them with the existing backend `golden_set.json`, prints hit rate, MRR, judge averages, and missing evidence cases, then exits nonzero if thresholds fail. Run it after changes to retrieval, corpus, prompt, or answer behavior. The scores are supplied by a controlled external evaluation run; this script does not call a provider or alter production behavior.

```powershell
python evaluate.py path\to\predictions.json --min-hit-rate 1 --min-mrr 0.5 --min-faithfulness 8 --min-relevance 8
```

## Integration boundary

The current node 02 response contains only `reply`; it has no request ID, route, evidence trace, or source versions. The current UI has no feedback buttons. Consequently this folder is ready to receive events and signals, but **the project's live answer path does not yet produce them**. Wiring the backend to emit audit events and return `request_id`, and wiring the UI to submit thumbs up/down, require changes in nodes 01/02/03/07 and are outside the permitted edit scope. Human review is required before any safety policy change based on these reports.
