# Environment

The orchestration service lives in `03_travel_ai_agent/agent_core/` and is imported by `02_api_backend/main.py` through `runtime.configure_module_paths()`.

| File | Responsibility |
|---|---|
| `main.py` | Entry point. `TravelAgent.ask_structured()` runs the whole flow for one request; `ask()` keeps the legacy string interface. |
| `schemas.py` | Data contracts: `OrchestrationRequest`, `RouteDecision`, `ToolCall`, `ToolResult`, `ExecutionPlan`, `ContextPackage`, `DecisionResult`, `OrchestrationResponse`, `AuditEvent`. |
| `classifier.py` | Intent analysis: route classification (LLM + keyword fallback), language detection, slot extraction (city / region / line). |
| `planner.py` | Execution logic: builds the `ExecutionPlan`, calls node 06 retrieval/rerank and runs the node 04 tool loop. |
| `tools.py` | Allow-listed node 04 adapters. Every adapter failure becomes an explicit `unavailable` snapshot. |
| `guardrails.py` | Validation gates: route enum, tool arguments (allow-list, caller toggles, argument format), tool results, node 07 decision output. |
| `context_manager.py` | Per-conversation memory keyed by `conversation_id`, history normalization, query reformulation/translation, package for node 07. |
| `llm_client.py` | The only provider client (Groq). Node 07 never performs network calls. |
| `audit.py` | Privacy-minimized audit event sent to node 08 after each answer. |
| `pipeline.py` | Backward-compatible alias (`RAGPipeline = TravelAgent`) for `02_api_backend/main.py`. |

## Configuration

Read from `02_api_backend/config.py` (`GROQ_API_KEY`, `LLM_MODEL`, `RETRIEVER_TOP_K`, `FINAL_TOP_K`, `USE_RERANK`, `USE_MEMORY`) plus optional `ROUTER_MODEL`.

Environment variables used only by this node:

| Variable | Purpose |
|---|---|
| `NODE08_AUDIT_URL` | `POST /audit` endpoint of node 08. When unset, audit events are logged locally. |
| `NODE08_AUDIT_TOKEN` | Value for the `X-Node08-Token` header. |

## Tests

```powershell
cd 03_travel_ai_agent
python -m pytest -q
```

The suite uses fakes for the provider, node 04, node 06 and node 08; it needs no API key, index files or ML models. Node 07's real `Generator` is used so the prompt/parse contract is exercised.
