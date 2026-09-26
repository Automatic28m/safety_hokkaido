# 📌 สรุปรายงานการพัฒนา: 03_travel_ai_agent (Safety Hokkaido)
**สรุปงาน, ขอบเขต PR, contract กับ node อื่น, ปัญหาที่พบ และผลทดสอบ**

---

## 🎯 1. ขอบเขตของงาน

PR นี้แก้หรือเพิ่มไฟล์ **เฉพาะใต้ `03_travel_ai_agent/`** เท่านั้น ไม่มีการแก้ไฟล์ของ node 01, 02, 04, 05, 06, 07, 08, `runtime.py`, `README.md` หรือ `.github/`

งานแก้ CI ของ AI PR reviewer ที่เคยอยู่ใน PR นี้ถูกย้ายไป branch แยก `ci/ai-reviewer-large-diff` แล้ว

node 03 บน `develop` เดิมใช้งานไม่ได้: `pipeline.py` ยังเรียก `Generator.generate()` ที่ node 07 ลบไปแล้ว และยังใช้ `global_memory` แบบ shared process ที่กฎห้าม งานนี้จึงเขียน node 03 ใหม่ตาม `03_travel_ai_agent_implementation_plan.md`

---

## 🧱 2. โครงไฟล์ใน `agent_core/`

| ไฟล์ | หน้าที่ |
|---|---|
| `main.py` | `TravelAgent.run()` จุดเข้าใช้งาน เดินตามลำดับที่แผนกำหนด; `ask_structured()` สำหรับ node 02, `ask()` แบบเดิม |
| `schemas.py` | `OrchestrationRequest`, `RouteDecision` (มี `fallback_used`), `ToolCall`, `ToolResult`, `ExecutionPlan`, `ContextPackage`, `DecisionResult`, `OrchestrationResponse`, `AuditEvent` |
| `classifier.py` | จัด route (LLM + keyword fallback ไทย/อังกฤษ), ตรวจภาษา, ดึง slot เมือง/เขต/สายรถไฟ |
| `planner.py` | สร้าง `ExecutionPlan`, เรียก node 06 retrieve/rerank, วน tool loop กับ node 04 |
| `tools.py` | allow-list ของ adapter node 04; ทุกความผิดพลาดกลายเป็น snapshot `unavailable` พร้อมเหตุผล |
| `guardrails.py` | ตรวจ 3 จุด: ก่อนเรียก tool, หลังได้ snapshot, หลังได้ decision จาก node 07 |
| `context_manager.py` | memory แยกตาม `conversation_id`, normalize history, reformulate/translate เฉพาะ retrieval query, สร้าง package ให้ node 07 |
| `llm_client.py` | client เดียวที่เรียก provider (Groq); node 07 ไม่แตะ network |
| `settings.py` | อ่านค่าจาก `config.py` ของ node 02 เมื่อ import ได้ มิฉะนั้นใช้ค่า default |
| `audit.py` | สร้างและส่ง `AuditEvent` ให้ node 08 (ไม่มีข้อความผู้ใช้/คำตอบ) |
| `pipeline.py` | `RAGPipeline = TravelAgent` ให้ `02_api_backend/main.py` import ได้เหมือนเดิม |
| `memory.py` | **shim เข้ากันได้ย้อนหลัง** สำหรับ `02_api_backend/main.py` ที่ยัง import `global_memory` — ไม่เก็บ history ใด ๆ มีแค่ `clear()` ที่ล้าง memory ทุก conversation |
| `query_transform.py` | **shim เข้ากันได้ย้อนหลัง** สำหรับ node 08 (`eval_retrieval.py`) ที่ยังเรียก `QueryTransformer().translate_to_english()` |

ไฟล์ที่ลบ: `router.py` (ไม่มี node อื่นใช้; logic ย้ายไป `classifier.py`)

### ลำดับการทำงาน (`main.py`)

```text
normalize history (API history เป็นหลัก)
  -> route / fallback (fallback_used)
  -> reformulate (เฉพาะ retrieval query)
  -> translate retrieval query (original_query ไม่ถูกแก้)
  -> retrieve / rerank (node 06)          [route มี rag]
  -> execute allowed tools (node 04)       [route มี realtime ∩ enabled_agents ∩ allow-list ∩ argument ถูกต้อง]
  -> build context package
  -> request decision (node 07 format_prompt -> llm_client -> node 07 parse_llm_response)
  -> validate decision (guardrails)
  -> remember per conversation_id
  -> emit audit event (node 08)
```

---

## 🔌 3. Contract ที่ node 03 ต้องการจาก node อื่น (ไม่ได้แก้แทนเจ้าของ)

| Node | สิ่งที่ node 03 ต้องการ | สถานะบน `develop` ตอนนี้ | node 03 ทำอย่างไรเมื่อยังไม่ตรง |
|---|---|---|---|
| **02** | ส่ง normalized request: `request_id`, `original_query`, `chat_history`, `enabled_agents`, `received_at` และ **optional** `conversation_id`, `locale` | ส่งครบยกเว้น `conversation_id` และ `locale` | ทำงานแบบ stateless (ไม่เก็บ server memory); ภาษาดูจากข้อความผู้ใช้ |
| **02** | เปลี่ยน import `global_memory` เป็น `memory_store.clear_all` | ยัง import `agent_core.memory.global_memory` | คง `memory.py` เป็น shim ที่ไม่มี shared history |
| **04** | adapter คืน `LiveDataSnapshot` (ไม่ใช่ string) พร้อม `status` ok/partial/stale/unavailable/mocked | `external_data` **import ไม่ได้**: `disaster.py` ใช้ `Tuple_Quake_Result` ก่อนบรรทัดที่นิยาม → `NameError` | ไม่เรียก tool ใด; ตอบ notice `node 04 adapters could not be imported (NameError ...)` และใช้ validator สำรองใน node 03; string → `INCOMPATIBLE_ADAPTER_OUTPUT` |
| **06** | evidence wrapper (`retrieve_response()`): results + rank/score/method + `index_version` + `retrieved_at` + `degraded`/`notices` | มีแล้ว | ใช้ wrapper เป็นหลัก; มีตัวอ่าน list แบบเก่าไว้ชั่วคราว; notices ที่สะสมข้าม request เอาแค่ 3 รายการล่าสุด |
| **07** | `format_prompt(original_query, history, evidence, live_data, tool_policy, language)` และ `parse_llm_response(json)`; ไม่เรียก network | มีแล้ว | ตรวจ interface ตอนเริ่ม ถ้าไม่มี → ไม่เริ่มระบบ (node 02 ตอบ 503) |
| **08** | รับ `AuditEvent` ผ่าน `POST /audit` + `X-Node08-Token` | มีแล้ว | ไม่ตั้ง `NODE08_AUDIT_URL` → log ในเครื่อง; ส่งไม่สำเร็จไม่กระทบคำตอบหลัก |

---

## ⚠️ 4. ปัญหาที่พบและวิธีแก้ (ภายใน node 03)

| ปัญหา | วิธีแก้ |
|---|---|
| orchestration เดิมเรียก `Generator.generate()` ที่ไม่มีแล้ว | node 03 เรียก provider เองผ่าน `llm_client.py` แล้วใช้ `format_prompt`/`parse_llm_response` ของ node 07 |
| `global_memory` แชร์ history ทุกผู้ใช้ | `ConversationMemoryStore` แยกตาม `conversation_id`; ไม่มี id = ไม่เก็บ; API history ชนะเสมอและใช้สร้าง memory ใหม่ทั้งชุด |
| router ตอบ `tools: []` แล้วเรียก tool ทุกตัว | `tool_hints=None` = ไม่รู้ (เรียกทุก tool ที่อนุญาต + notice), list = เรียกเฉพาะที่ระบุ |
| `degraded` ติด true ทุกครั้งเพราะ train เป็น `mocked` | `unavailable/stale/partial` ทำให้ degraded เสมอ; `mocked` เฉพาะเมื่อ node 07 ระบุว่าใช้ source นั้น |
| decision ที่ `used_evidence_ids` เป็น `null`/ตัวเลข ถูก node 07 ปฏิเสธ → 503 | normalize ชนิดข้อมูลก่อนส่ง node 07 parse; guardrails ยังกรอง id ที่ไม่ได้ส่งให้จริง |
| keyword สั้น (`jr`, `wind`, `119`, `live`) จับคำอื่น | คำ ≤ 4 ตัว/ตัวเลขต้องตรงทั้งคำ; ตัด `live`; ยุบช่องว่างซ้ำ |
| ตัดคำตอบเกิน 8000 ตัวอักษรแบบเงียบ | เพิ่ม notice เมื่อถูกตัด |
| node 02/08 ยัง import `agent_core.memory` / `agent_core.query_transform` | คงไว้เป็น shim ใน node 03 แทนการแก้ไฟล์ของ node นั้น |
| unit test เดิมพึ่ง node 04/07 ของจริง | unit test ใช้ fake ผ่าน dependency injection ทั้งหมด; ทดสอบกับของจริงแยกไว้ใน `tests/test_contracts.py` ที่ skip พร้อมบอกเจ้าของเมื่อ node นั้นใช้ไม่ได้ |

---

## 📊 5. ผลการทดสอบ

```text
03_travel_ai_agent  python -m pytest -q -rs      97 passed, 2 skipped
  skipped: node 04 `external_data` cannot be imported: NameError ... (owner: node 04)
02_api_backend      python -m pytest -q          43 passed   (ไม่ได้แก้ไฟล์ node 02)
python -m compileall 02..08 + runtime.py         OK
```

| ชุดทดสอบ | สิ่งที่ครอบคลุม |
|---|---|
| unit tests (8 ไฟล์) | memory isolation, API history override, fallback trace, tool ที่ถูกปิด/allow-list, snapshot ทุกสถานะ, original query/evidence/live data/language ส่งให้ node 07, provider ล่ม → unavailable |
| `test_scope_and_compat.py` | shim `global_memory`/`QueryTransformer`, adapter คืน string, node 04 import ไม่ได้, wrapper ของ node 06, ตรวจ interface ของ node 07, original query ไม่ถูกแก้ |
| `test_contracts.py` | ทดสอบกับของจริงของ node 02 (HTTP 200/503), 04, 06, 07, 08 (`validate_audit`) |

การตรวจเพิ่ม: เมื่อจำลอง node 04 ที่แก้ `NameError` แล้ว (สำเนาชั่วคราว ไม่ได้ commit) contract ของ node 04 ผ่านครบ และ validator สำรองให้ค่า default ตรงกับของ node 04

Smoke test ผ่าน `02_api_backend/main.py` ที่ไม่ได้แก้: แอปบูตได้, `POST /ask` ไม่มี API key คืน HTTP 503 พร้อม notice ที่บอกเหตุผลครบ รวมถึง `node 04 adapters could not be imported`

---

## ✅ 6. เกณฑ์รับ PR

| เกณฑ์ | สถานะ |
|---|---|
| diff มีเฉพาะ `03_travel_ai_agent/**` | ✅ |
| ไม่มี `global_memory` shared process | ✅ (`memory.py` เป็น reset handle ที่ไม่เก็บข้อมูล) |
| history ที่ API ส่งมามี precedence สูงสุด | ✅ |
| route/fallback/tool policy trace ได้ | ✅ `fallback_used`, notices, `tool_policy`, audit route |
| tool ที่ปิดไม่ถูกเรียก | ✅ |
| original query ไม่ถูกแก้ระหว่าง reformulate/translate | ✅ |
| provider/index/node 07 ใช้ไม่ได้ → degraded/unavailable อย่างซื่อสัตย์ | ✅ |
| test memory isolation และ policy tests ผ่าน | ✅ |
| ไม่มี AI watermark หรือ AI contributor ใน source/commit/PR | ✅ |

---

## 🔭 7. สิ่งที่ต้องให้เจ้าของ node อื่นทำ

* **Node 04:** ย้ายบรรทัด `Tuple_Quake_Result = Any` / `Tuple_Warning_Result = Any` ใน `external_data/disaster.py` ขึ้นไปก่อนฟังก์ชันที่ใช้ — ตอนนี้ import ทั้ง package ไม่ได้ ทำให้ live data ทุกตัวใช้ไม่ได้
* **Node 02:** (ถ้าต้องการ memory ต่อบทสนทนา) รับ `conversation_id` แบบ optional แล้วส่งต่อใน normalized request; และเปลี่ยน import เป็น `memory_store.clear_all`
* **Node 01:** ส่ง `conversation_id` และแสดง `notices` / `degraded` ให้ผู้ใช้เห็น
* **Node 08:** เปลี่ยนไปใช้ `ContextManager.translate_for_retrieval()` แทน `QueryTransformer` เมื่อสะดวก
* **CI:** merge branch `ci/ai-reviewer-large-diff` ก่อน เพื่อให้ AI reviewer อ่าน diff ขนาดใหญ่ของ PR นี้ได้
