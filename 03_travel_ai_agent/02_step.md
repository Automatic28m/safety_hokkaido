# Agent flow

The order below is fixed. Each step records its outcome in `notices` so the response is auditable.

1. **Receive** the validated request from node 02 (`request_id`, optional `conversation_id`, `original_query`, `chat_history`, `enabled_agents`). `original_query` is never modified.
2. **Resolve history.** History sent by the API is authoritative. Server memory is read only when no history was sent and a `conversation_id` is present; a request can never read another conversation.
3. **Route** with `classifier.classify_message()`. The result must be one of `general`, `rag`, `realtime`, `rag+realtime`. If the router fails or is unsure, keyword rules decide and `fallback_used` is set; with no keyword match the conservative default is `rag`.
4. **Reformulate** a follow-up into a standalone question (retrieval only) when history exists.
5. **Translate** the retrieval query to English when the user did not write in English. The user's text is not translated.
6. **Plan.** `planner.plan()` decides whether node 06 is called and which node 04 tools are permitted: route allows live data, the caller did not disable the tool, the adapter is on the allow-list, and the argument passes `guardrails.validate_tool_args()`. Missing slots use conservative defaults (Sapporo / Hokkaido / All) with a notice.
7. **Retrieve** from node 06 (`retrieve` then `rerank`) when the route includes `rag`. Otherwise evidence is explicitly empty.
8. **Call tools** from node 04 when the route includes `realtime`. Every snapshot is kept, including `unavailable`, `stale`, `partial` and `mocked`, and each one produces a notice through `guardrails.validate_tool_result()`.
9. **Build the context package** (`original_query`, windowed history, evidence, live snapshots, language, tool policy) and hand it to node 07 `format_prompt()`.
10. **Generate** by sending the formatted messages to the provider through `llm_client.py`; node 07 `parse_llm_response()` validates the JSON. A provider outage returns `status: "unavailable"` (node 02 maps it to HTTP 503). No imitation reply is produced.
11. **Guard the decision** with `guardrails.validate_decision()`: sanitize HTML, restrict `used_evidence_ids` / `used_live_sources` to what was actually supplied, propagate `degraded`. `unavailable`, `stale` and `partial` snapshots always degrade the answer; a `mocked` snapshot degrades it only when the decision relied on that source.
12. **Remember** the exchange in the memory of this `conversation_id` only.
13. **Emit an audit event** to node 08 (`request_id`, timestamp, route, degraded, evidence IDs, source versions, index version). No query or reply text is included.

## Sequence with node 02

```text
02 API ─ask_structured(normalized)─▶ main.py
   main.py ─▶ classifier.classify_message ─▶ RouteDecision
   main.py ─▶ context_manager.reformulate_query / translate_for_retrieval
   main.py ─▶ planner.plan ─▶ ExecutionPlan
   planner ─▶ node 06 retrieve/rerank            (route has rag)
   planner ─▶ guardrails.validate_tool_args ─▶ tools.execute ─▶ guardrails.validate_tool_result   (route has realtime)
   main.py ─▶ context_manager.build_context_package ─▶ node 07 format_prompt ─▶ llm_client ─▶ node 07 parse_llm_response
   main.py ─▶ guardrails.validate_decision ─▶ context_manager.remember ─▶ audit.emit (node 08)
02 API ◀─OrchestrationResponse (status, reply, route, degraded, notices, evidence, live_sources, safety_level)─
```
