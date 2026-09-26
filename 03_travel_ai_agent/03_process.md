# Safety constraints

- Routing is an optimization, never the final safety authority. Neither the route nor a retrieval score is ever used to conclude that a situation is safe.
- Every fallback (router error, low confidence, translation or reformulation failure, adapter failure, reranker failure) is recorded in `notices` and, where applicable, in `fallback_used` or `degraded`. Nothing degrades silently.
- Node 03 selects and calls tools; node 07 only receives verified evidence and snapshots. Node 07 never calls a provider or a network tool.
- A tool is called only when all of the following hold: the route permits live data, the caller did not disable it in `enabled_agents`, the adapter is on the allow-list, and the argument passed validation.
- Snapshots with status `unavailable`, `stale`, `partial` or `mocked` are passed to node 07 unchanged and surfaced to the user as notices; they are never presented as live facts.
- If the decision provider is unavailable or returns an unparseable decision twice, the response is `status: "unavailable"`; no reply that imitates a real answer is generated.
- Memory is scoped to a single `conversation_id`. Requests without a `conversation_id` leave no server-side memory. History supplied by the API always overrides server memory.
- The audit event sent to node 08 contains identifiers and versions only; no query text, reply text or user identifier.
- No AI watermark or AI contributor attribution is added to anything committed to the repository.

## Ownership

- This node changes files under `03_travel_ai_agent/` only. Needs from other nodes are written as contracts in `03_travel_ai_agent_work_report.md`, never patched here.
- When a neighbouring node breaks its contract (import error, plain-text adapter output, missing interface), node 03 reports it through `notices`, `degraded` or `status: "unavailable"` instead of working around it silently.

## Acceptance checklist

| Requirement | How it is verified |
|---|---|
| Histories of two conversations never cross | `tests/test_context_manager.py`, `tests/test_main.py::test_memory_is_isolated_per_conversation_and_api_history_wins` |
| API history is not overwritten by server state | same tests (`api` source wins over `memory`) |
| Route and fallback are traceable | `fallback_used` in the response, notices, audit event route; `tests/test_classifier.py` |
| A tool the caller disabled is never called | `tests/test_planner.py::test_disabled_tool_is_skipped_and_never_called`, `tests/test_main.py::test_caller_disabled_tool_is_never_called` |
| Provider outage yields `unavailable`, not a fake reply | `tests/test_main.py::test_decision_provider_down_returns_unavailable_without_fake_reply` |
| Node 07 output references only supplied evidence | `tests/test_guardrails.py`, `tests/test_main.py::test_decision_referencing_unknown_evidence_is_cleaned` |
| The diff touches only `03_travel_ai_agent/**` | `git diff --name-only origin/develop...HEAD` |
| Unit tests do not depend on other nodes | only `03_travel_ai_agent` on `sys.path`; fakes injected (`tests/conftest.py`) |
| Broken neighbouring nodes are reported, not patched | `tests/test_scope_and_compat.py`, skipped contract tests name the owner |
