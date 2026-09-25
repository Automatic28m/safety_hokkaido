# 📌 สรุปรายงานการพัฒนา: 03_travel_ai_agent (Safety Hokkaido)
**เอกสารสรุปผลการดำเนินงาน, ปัญหาที่พบ, การแก้ไข, และการเชื่อมต่อกับโมดูล 02 / 04 / 06 / 07 / 08**

---

## 🎯 1. สิ่งที่พัฒนาและปรับปรุงทั้งหมด (What Was Done)

โมดูล 03 บน branch `develop` เดิมยังเป็นโค้ดที่ย้ายมาจาก `02_api_backend/src` (`router.py`, `pipeline.py`, `query_transform.py`, `memory.py`) ซึ่ง **ใช้งานจริงไม่ได้** เพราะยังเรียก `Generator().generate(...)` ที่โมดูล 07 ลบทิ้งไปแล้ว และยังใช้ `global_memory` ที่กฎสถาปัตยกรรมห้าม งานรอบนี้จึงเขียนโมดูล 03 ใหม่ทั้งหมดตาม `03_travel_ai_agent_implementation_plan.md` โดยจัดโครงไฟล์ตามผังหน้าที่ (File & Function Responsibilities) และ sequence diagram ของ AI Router / Agent

### 1.1 โครงไฟล์ใหม่ใน `agent_core/`

| ไฟล์ | หน้าที่ | ฟังก์ชัน/คลาสหลัก |
|---|---|---|
| `main.py` | จุดเข้าใช้งาน (entry point) รับ request จากโมดูล 02 แล้วเดินตามลำดับที่แผนกำหนด | `TravelAgent.ask_structured()`, `TravelAgent.ask()` (legacy), `TravelAgent.run()` |
| `schemas.py` | Data contracts ทุกตัวที่ข้าม boundary | `OrchestrationRequest`, `RouteDecision` (มี `fallback_used`), `ToolCall`, `ToolResult`, `ExecutionPlan`, `ContextPackage`, `DecisionResult`, `OrchestrationResponse`, `AuditEvent` |
| `classifier.py` | วิเคราะห์ intent | `classify_message()` (LLM + keyword fallback), `detect_context_needs()`, `extract_slots()`, `missing_required_slots()`, `detect_language()` |
| `planner.py` | ตรรกะการทำงาน | `plan()` สร้าง `ExecutionPlan`, `retrieve()` เรียกโมดูล 06, `execute_tools()` วน tool loop กับโมดูล 04 |
| `tools.py` | Allow-list ของ adapter โมดูล 04 | `ToolExecutor.execute()` แปลงทุก error เป็น snapshot `unavailable` |
| `guardrails.py` | ด่านตรวจความปลอดภัย 3 จุด | `validate_tool_args()`, `validate_tool_result()`, `validate_decision()`, `validate_route()` |
| `context_manager.py` | จัดการบริบทสนทนา | `ConversationMemoryStore` (แยกตาม `conversation_id`), `resolve_history()`, `reformulate_query()`, `translate_for_retrieval()`, `build_context_package()` |
| `llm_client.py` | client เดียวในระบบที่คุยกับ Groq | `GroqChatClient.complete()`, `extract_json_object()` |
| `audit.py` | ส่ง trace ให้โมดูล 08 | `build_audit_event()`, `AuditEmitter.emit()` |
| `pipeline.py` | alias เพื่อความเข้ากันได้ (`RAGPipeline = TravelAgent`) | โมดูล 02 `main.py` import ได้เหมือนเดิม |

ไฟล์ที่ลบออก: `router.py`, `query_transform.py`, `memory.py` (ถูกรวมเข้า `classifier.py` และ `context_manager.py`)

### 1.2 ลำดับการทำงานตาม sequence diagram (`main.py`)

```text
02 API ──ask_structured(normalized)──▶ main.py
  1. resolve_history      (API history เป็นหลัก; memory ใช้เฉพาะ conversation เดียวกัน)
  2. classify_message     → RouteDecision (route ∈ enum, fallback_used)
  3. reformulate_query    → standalone query (ใช้ค้นหาเท่านั้น; original query คงเดิม)
  4. translate_for_retrieval → English query (แปลเฉพาะ retrieval query)
  5. planner.plan         → ExecutionPlan (ตรวจ route + enabled_agents + allow-list + argument)
  6. planner.retrieve     → โมดูล 06 retrieve / rerank      [เมื่อ route มี rag]
  7. planner.execute_tools→ guardrails.validate_tool_args → tools.execute → guardrails.validate_tool_result   [เมื่อ route มี realtime]
  8. build_context_package→ โมดูล 07 format_prompt → llm_client → โมดูล 07 parse_llm_response
  9. guardrails.validate_decision (ตัด HTML, กรอง evidence/live source ที่ไม่ได้ส่งให้จริง)
 10. context_manager.remember (เฉพาะ conversation_id นี้)
 11. audit.emit → โมดูล 08 (ไม่มีข้อความผู้ใช้/คำตอบ)
02 API ◀──OrchestrationResponse (status, reply, route, degraded, notices, evidence, live_sources, safety_level, fallback_used)
```

### 1.3 การเชื่อมต่อกับโมดูลอื่น

* **โมดูล 02:** รองรับ `pipeline.ask_structured(normalized_dict)` ตาม contract ของ `api/endpoints.py` ครบทุกฟิลด์ (`status`, `reply`, `route`, `degraded`, `notices`, `evidence`, `live_sources`) และคง `ask()` แบบเดิม; provider ล่มคืน `status: "unavailable"` ให้โมดูล 02 map เป็น HTTP 503
* **โมดูล 04:** เรียกเฉพาะ adapter ที่ผ่าน allow-list + `enabled_agents` + validator ของโมดูล 04 (`validate_city / validate_region / validate_line_name`) และเก็บ `LiveDataSnapshot` ทุกสถานะ (`ok / partial / stale / unavailable / mocked`)
* **โมดูล 06:** เรียก `HybridRetriever.retrieve()` + `Reranker.rerank()` และแปลง `RetrievalResultItem` เป็น dict ที่โมดูล 07 อ่านได้ (`chunk_id`, `text`, `metadata`, `rank`, `score`, `retrieval_method`); index ไม่พร้อม → `degraded: true` พร้อม notice
* **โมดูล 07:** ส่ง original query, history, evidence, live snapshots, `tool_policy`, `language` ให้ `Generator.format_prompt()` แล้วนำผลจาก provider ส่งกลับ `parse_llm_response()`; โมดูล 07 ไม่แตะ network
* **โมดูล 08:** ส่ง `AuditEvent` (`request_id`, `timestamp`, `route`, `degraded`, `evidence_ids`, `source_versions`, `evaluation_schema_version`, `index_version`) ผ่าน `NODE08_AUDIT_URL` + `NODE08_AUDIT_TOKEN`; ไม่ตั้งค่าจะ log ภายในแทน และไม่มีวัน throw

### 1.4 ชุดทดสอบอัตโนมัติ (`tests/`, 66 test cases)

| ไฟล์ | จำนวน | ครอบคลุม |
|---|---|---|
| `test_schemas.py` | 10 | enum ของ route/tool, `enabled_agents` ต่อ request, `AuditEvent` ปฏิเสธฟิลด์เกิน |
| `test_classifier.py` | 11 | keyword ไทย/อังกฤษ, low-confidence fallback, provider ล่ม, slot ภาษาไทย |
| `test_context_manager.py` | 10 | history 2 conversation ไม่ข้ามกัน, API history ชนะ memory, summarization, LRU |
| `test_guardrails.py` | 7 | tool ที่ถูกปิดไม่ถูกเรียก, argument ไม่ปลอดภัย, ตัด HTML, กรอง evidence ปลอม |
| `test_planner.py` | 10 | route → plan, adapter พัง → `unavailable`, retriever/reranker ล่ม → degraded |
| `test_tools_and_audit.py` | 4 | normalize snapshot, audit event ไม่มีข้อความผู้ใช้ |
| `test_main.py` | 13 | end-to-end ทุก route กับ Generator จริงของโมดูล 07, provider ล่ม → `unavailable`, memory isolation |

---

## ⚠️ 2. ปัญหาที่พบระหว่างทางและวิธีแก้ไข (Problems & Solutions)

| ปัญหาที่พบ | สาเหตุ | วิธีการแก้ไข |
|---|---|---|
| **1. โมดูล 03 บน develop ใช้งานไม่ได้** | `pipeline.py` เรียก `Generator.generate()` ที่โมดูล 07 ลบไปแล้ว | เขียน orchestration ใหม่ให้ใช้ `format_prompt` / `parse_llm_response` ของโมดูล 07 และให้โมดูล 03 เป็นผู้เรียก provider เอง |
| **2. `global_memory` ผิดกฎ** | history ทั้ง process แชร์กันทุกผู้ใช้ | `ConversationMemoryStore` แยกตาม `conversation_id`; request ที่ไม่มี `conversation_id` ไม่เก็บ memory เลย; `02_api_backend/main.py` เปลี่ยนมาใช้ `memory_store.clear_all` สำหรับ debug endpoint |
| **3. โมดูล 04 import ไม่ได้ทั้ง package** | `disaster.py` ใช้ `Tuple_Quake_Result` เป็น return annotation ก่อนบรรทัดที่นิยาม → `NameError` ตอน import ทำให้ tool ทุกตัวใช้ไม่ได้ | ย้ายบรรทัดนิยาม alias ขึ้นไปก่อนการใช้งาน (แก้ 2 บรรทัดในโมดูล 04) และให้ `tools.py`/`guardrails.py` ของโมดูล 03 ทนต่อ import ล้มเหลว (degrade แทน crash) |
| **4. keyword `rain` จับคำว่า `train`** | จับ substring ตรง ๆ | ใช้ regex แบบขึ้นต้นคำสำหรับคำภาษาอังกฤษ (ยังจับ `snowing` จาก `snow` ได้) และ substring สำหรับภาษาไทย |
| **5. `store or memory_store` เลือกผิดตัว** | `ConversationMemoryStore` มี `__len__` ทำให้ store ว่างเป็น falsy | เปลี่ยนเป็น `store if store is not None else memory_store` ทุกจุด |
| **6. tool ถูกเรียกครบทุกตัวแม้ไม่เกี่ยว** | pipeline เดิมเปิด weather/disaster/train ทั้งหมดเมื่อ route เป็น realtime | router คืน `tool_hints` (LLM + keyword) และ planner เรียกเฉพาะ tool ที่จำเป็น ∩ `enabled_agents` ∩ allow-list |

---

## 📊 3. ผลการทดสอบ (Test Results)

```text
03_travel_ai_agent   python -m pytest -q      66 passed
02_api_backend       python -m pytest -q      43 passed   (contract ของ /ask ไม่เปลี่ยน)
04_external_data_services  pytest (PYTHONPATH=02,04)   63 passed, 1 failed*
python -m compileall 02..08 + runtime.py      OK
```

\* `test_08_reexport_via_backend_src_tools` ของโมดูล 04 ล้มเหลวอยู่แล้วบน develop ก่อนหน้านี้ (ตรวจฟังก์ชันใน `02_api_backend/src/tools.py` รุ่นเก่า) ไม่เกี่ยวกับงานรอบนี้

Smoke test จริงผ่าน `02_api_backend/main.py` (เครื่องที่ไม่มี faiss และไม่มี `GROQ_API_KEY`): แอปบูตได้, pipeline เป็น `TravelAgent`, `POST /ask` คืน **HTTP 503** พร้อม notices ที่บอกสาเหตุครบ (`router fallback used`, `retrieval is not available`, `decision provider unavailable`) แทนการตอบ 200 พร้อมข้อความ error

---

## ✅ 4. รีเช็คตามเกณฑ์รับงานใน implementation plan

| เกณฑ์ | สถานะ | หลักฐาน |
|---|---|---|
| history ของสอง conversation ไม่ข้ามกัน | ✅ | `test_two_conversations_never_share_history`, `test_memory_is_isolated_per_conversation_and_api_history_wins` |
| API history ไม่ถูก server global state ทับ | ✅ | `test_api_history_is_authoritative_over_memory` |
| route/fallback trace ได้ | ✅ | `fallback_used` ใน response + notice + audit event (`test_router_fallback_is_flagged_and_logged_in_response`) |
| tool ที่ caller ปิดไม่ถูกเรียก | ✅ | `test_disabled_tool_is_skipped_and_never_called`, `test_caller_disabled_tool_is_never_called` |
| validate route enum | ✅ | `RouteDecision` + `guardrails.validate_route` |
| ลำดับ normalize → route → reformulate → translate → retrieve → tools → generate → audit | ✅ | `TravelAgent.run()` + `test_node07_receives_original_query_evidence_live_data_and_language` |
| ส่ง original query, history, evidence, live snapshots, tool policy, language ให้โมดูล 07 | ✅ | `ContextPackage` → `Generator.format_prompt()` |
| ห้ามใช้ route/score ตัดสินว่า safe | ✅ | โมดูล 03 ไม่สร้าง `safety_level` เอง รับจากโมดูล 07 และ validate เท่านั้น |
| ห้ามให้ generator เรียก provider โดยตรง | ✅ | provider call อยู่ใน `llm_client.py` ของโมดูล 03 เท่านั้น |
| ห้ามมี AI watermark / AI contributor | ✅ | ไม่มีในโค้ด, เอกสาร และ commit |

---

## 🔭 5. งานที่เหลือนอกขอบเขตโมดูล 03

* โมดูล 02 ยังไม่ส่ง `conversation_id` มาใน `NormalizedAskRequest` (โมดูล 03 รองรับแล้ว เป็น optional) — เมื่อโมดูล 01/02 ส่งมา memory ต่อ conversation จะทำงานทันที
* โมดูล 01 ยังอ่านเฉพาะ `reply`; ฟิลด์ `notices`, `degraded`, `evidence`, `live_sources` พร้อมให้ UI แสดงสถานะ unavailable/stale/mocked ตามกฎของโมดูล 01
* การส่ง audit ไปโมดูล 08 ต้องตั้ง `NODE08_AUDIT_URL` และ `NODE08_AUDIT_TOKEN` ใน `.env` ของ backend เมื่อ deploy โมดูล 08 แล้ว
