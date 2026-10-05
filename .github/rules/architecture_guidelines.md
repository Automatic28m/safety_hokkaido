# Safety Hokkaido: สัญญาโครงสร้างและการเชื่อมต่อของ AI Nodes

เอกสารนี้เป็น **integration contract** สำหรับให้ AI/ทีมที่รับผิดชอบแต่ละ node วิเคราะห์และเพิ่ม feature ได้อย่างอิสระ แต่ยังเชื่อมและรันร่วมกันได้
กฎเหล็ก
จะนำงานลง Github ทุกคนห้ามติดลายน้ำ AI ใดๆ หรือ Contributor AI ใดๆ เด็ดขาด!!

อ้างอิง source branch `main` commit `b0442a677bcbd1927ac5855e54cb01bc383b9e70` (ตรวจเมื่อ 2026-09-24)

## 1. ภาพรวมระบบและขอบเขต

```text
Browser
  -> 01_web_app (Next.js)
  -> POST /api/chat (Next.js proxy)
  -> POST /ask (02_api_backend / FastAPI)
  -> 03_travel_ai_agent (orchestrator)
       -> 04_external_data_services   (weather / disaster / train)
       -> 05_data_integration         (build index)
       -> 06_risk_knowledge_services  (retrieve / rerank evidence)
       -> 07_decision_llm_engine      (grounded answer + tool calls)
  -> 08_recommendation_feedback       (evaluation / future feedback)
  -> Browser
```

ใน `main` ปัจจุบัน node 03–08 **ยังไม่ได้แยกเป็น package/service**: implementation อยู่ใน `02_api_backend/src/` และ `02_api_backend/evaluation/` ดังนี้

| Node | ความรับผิดชอบ | Source ปัจจุบัน | สิ่งที่ห้ามทำ |
|---|---|---|---|
| 01 Web app | UI, locale, แชต, แสดงผล | `01_web_app/src/` | ไม่ตัดสิน safety, ไม่เก็บ LLM/API key |
| 02 API backend | HTTP, validation, CORS, health/auth | `02_api_backend/main.py` | ไม่ใส่ business decision ของ node 03–07 |
| 03 Travel AI agent | route, context, orchestration | `router.py`, `rag_pipeline.py`, `query_transform.py`, `memory.py` | ไม่สร้างคำตอบ safety เอง |
| 04 External data | เรียก provider และ normalize live snapshot | `tools.py` | อย่าเรียกข้อมูล mock ว่า live |
| 05 Data integration | โหลด corpus, chunk, embed, build index | `document_loader.py`, `text_splitter.py`, `embedding_model.py`, `vector_store.py` | อย่าปนเว็บที่ยังไม่ review เข้า corpus |
| 06 Risk knowledge | retrieve/rerank evidence พร้อม provenance | `hybrid_retriever.py`, `rerankers.py` | ไม่ตัดสินว่าปลอดภัยหรือไม่ |
| 07 Decision LLM | grounded response และ guardrail | `generator.py`, `config.py` | ไม่สร้าง warning/คำแนะนำ/แหล่งอ้างอิงขึ้นเอง |
| 08 Feedback | evaluation, feedback, audit | `evaluation/` | ห้ามปรับ safety behavior อัตโนมัติจาก feedback |

## 2. กติกากลางที่ทุก node ต้องยึด

1. สื่อสารข้าม node เป็น JSON-serializable object; ไม่ส่ง object ของ framework, model หรือ database connection ข้ามขอบเขต
2. เก็บข้อความดิบของผู้ใช้ (`original_query`) เสมอ; translation/reformulation เป็นข้อมูลอนุพันธ์ ห้ามทับต้นฉบับ
3. ทุก evidence และข้อมูลสดต้องมี provenance และเวลา (`retrieved_at`/`fetched_at`) ก่อนถึง node 07
4. ความล้มเหลวของ dependency ต้องเป็นผลลัพธ์แบบ `degraded` ที่อธิบายได้ ไม่ใช่ fabricated success
5. `role` ของข้อความรองรับเพียง `user`, `assistant`, `system`, `tool`; ให้แปลง legacy `ai` เป็น `assistant` ที่ API boundary
6. ข้อมูล safety ต้อง fail conservatively: หากหา evidence/live data ไม่ได้ ให้บอกข้อจำกัดอย่างชัดเจนและไม่สรุปว่า “safe”
7. เปลี่ยน schema แบบ backward compatible ก่อน: เพิ่ม field ได้, ห้ามเปลี่ยนความหมาย/type ของ field เดิมโดยไม่ version endpoint/contract

## 3. สัญญา HTTP ระหว่าง node 01 และ 02

### 3.1 Request ที่ canonical: `POST /ask`

`01_web_app/src/app/api/chat/route.js` ส่ง payload ผ่านไปยัง backend เกือบตรงตัว จึงต้องถือ schema นี้เป็น source of truth

```json
{
  "message": "optional legacy single query",
  "messages": [
    { "role": "user", "content": "Is it safe to travel to Sapporo today?" },
    { "role": "assistant", "content": "..." }
  ],
  "enabled_agents": {
    "weather": true,
    "disaster": true,
    "train": true
  }
}
```

Validation/meaning:

| Field | Type | Required | Rule |
|---|---|---:|---|
| `message` | non-empty string | one of `message`/`messages` | legacy mode only |
| `messages` | non-empty array of `ChatMessage` | one of `message`/`messages` | last message must be a non-empty `user` message |
| `ChatMessage.role` | enum | yes | `user`, `assistant`, `system`, `tool`; accept `ai` only as legacy alias |
| `ChatMessage.content` | string | yes | user-visible text; no timestamp required for backend |
| `enabled_agents` | object | no | missing key means **enabled**; explicit `false` only disables that tool |

Do not use a mutable object default in request models. Create a new default dictionary per request.

### 3.2 Response ที่ควรยึดเป็นเป้าหมาย

`main.py` ตอนนี้ตอบเพียง `{ "reply": "..." }` และ frontend พึ่ง field นี้อยู่ จึงต้องเก็บไว้เสมอ. เพิ่ม trace ได้ดังนี้:

```json
{
  "reply": "ข้อความคำตอบ Markdown ที่แสดงผู้ใช้ได้",
  "request_id": "uuid",
  "status": "ok",
  "route": "rag+realtime",
  "degraded": false,
  "notices": [],
  "evidence": [
    {
      "chunk_id": "jnto_earthquake_advices.json_0_part_0",
      "source_file": "jnto_earthquake_advices.json",
      "url": "https://…",
      "retrieved_at": "2026-09-24T10:00:00Z"
    }
  ],
  "live_sources": []
}
```

HTTP semantics: invalid request = `400` with `detail`; pipeline dependency unavailable = `503`; unexpected backend failure = `500`. อย่าส่ง error ออกมาใน `reply` พร้อม HTTP 200 เพราะ frontend/monitoring จะแยกความสำเร็จออกไม่ได้.

### 3.3 Node 01 presentation contract

- ส่ง `messages` โดยไม่จำเป็นต้องส่ง timestamp; timestamp เป็น UI-only
- แสดง `reply` เป็น Markdown แบบ sanitize แล้ว
- แสดง `notices`/`degraded` ให้ผู้ใช้เห็น; ห้ามซ่อนความล้มเหลวของข้อมูลสด
- หากเพิ่ม agent toggle ใน UI ต้องส่งครบทั้ง `weather`, `disaster`, `train`; ปัจจุบัน `ChatBot.jsx` ส่งแค่สองตัว ทำให้ train ใช้ค่า default จาก backend
- ตั้ง `BACKEND_API_URL` ใน `.env.local`; ห้าม hard-code URL production หรือ secret ฝั่ง browser

## 4. สัญญาภายในของ node 03 (orchestration)

### 4.1 `RouteDecision`

```json
{
  "route": "general | rag | realtime | rag+realtime",
  "confidence": 0.0,
  "reasoning": "short auditable reason",
  "fallback_used": false
}
```

`router.py` ใช้ Groq แล้ว fallback จาก keyword; node ที่แก้ router ต้องคืน route ใน enum เท่านั้น และต้องบันทึกเมื่อ fallback ทำงาน. Route เป็นตัวเลือกการเรียก dependency ไม่ใช่คำตัดสิน safety.

### 4.2 `OrchestrationRequest`

```json
{
  "request_id": "uuid",
  "original_query": "ข้อความผู้ใช้",
  "chat_history": [{ "role": "user", "content": "…" }],
  "enabled_agents": { "weather": true, "disaster": true, "train": true },
  "locale": "th",
  "received_at": "ISO-8601"
}
```

ลำดับที่ต้องคงไว้: normalize history -> route -> reformulate (หากมี history) -> translate สำหรับ retrieval -> retrieve/rerank ตาม route -> เปิดเฉพาะ live tools ที่ route และ caller อนุญาต -> generate -> append memory/evaluation event.

### 4.3 กฎ memory สำคัญ

ในโค้ดปัจจุบัน เมื่อ `USE_MEMORY=True`, `RAGPipeline.ask()` แทนที่ `chat_history` ที่ API ส่งด้วย `global_memory` ซึ่งเป็น state ร่วมทั้ง process. นี่ทำให้ history ของผู้ใช้หลายรายรั่วข้ามกันได้ และ frontend history ไม่ได้ถูกใช้จริง.

Contract ใหม่: memory ต้องมี `conversation_id`/session scope; API history เป็น authoritative เมื่อส่งมา; server memory เป็น optional cache/summarization ของ conversation เดียวกันเท่านั้น. ห้ามใช้ global memory สำหรับ production multi-user.

## 5. สัญญา node 04: External data services

ทุก adapter รับ validated input และคืน `LiveDataSnapshot` ไม่คืนเพียง string:

```json
{
  "provider": "JMA",
  "kind": "disaster_warning",
  "scope": { "region": "Hokkaido" },
  "status": "ok | unavailable | stale | partial | mocked",
  "fetched_at": "ISO-8601",
  "expires_at": "ISO-8601",
  "data": { "summary": "…", "items": [] },
  "source_url": "https://official-source.example/",
  "error_code": null
}
```

| Tool | Input | ปัจจุบัน | ข้อกำหนดก่อน production |
|---|---|---|---|
| `get_real_time_weather(city)` | `city: string` | weather provider ใน `tools.py` | timeout, normalize units, official URL/provider และ `fetched_at` |
| `get_disaster_warnings(region)` | `region: string` | JMA quake list + snow statement แบบ hard-coded | แยก JMA result จาก synthetic statement และคืน `partial` เมื่อดึงได้ไม่ครบ |
| `check_train_status(line_name)` | `line_name: string` | simulated response | ต้องคืน `status: mocked` จนกว่าจะใช้ verified JR Hokkaido adapter; node 07 ห้ามเรียกว่า live |

Provider error ต้องคืน snapshot `unavailable` พร้อม safe user-facing notice; ห้ามคืน "No warnings" เมื่อ request/provider ล้มเหลว.

## 6. สัญญา node 05: Data integration

### 6.1 Input/output ของ index build

Input: vetted `data/*.pdf`, `*.txt`, `*.json` (ยกเว้น `golden_set.json`).

Output ที่ `vector_db/`:

- `document.index` — FAISS index
- `bm25_index.pkl` — lexical index
- `chunk_store.json` — canonical mapping ตามลำดับ index
- `index_meta.json` — fingerprint ของ corpus

`document.index`, BM25 และ `chunk_store.json` ต้องถูก publish/rebuild เป็นชุดเดียวกัน; ห้าม deploy ข้ามรุ่น. Build ที่สำเร็จต้องเขียน manifest เพิ่ม: corpus hash, embedding model, chunk parameters, build time และ schema version.

### 6.2 `EvidenceChunk` canonical schema

```json
{
  "chunk_id": "stable-id",
  "text": "ข้อความจากแหล่งที่ตรวจแล้ว",
  "metadata": {
    "source_file": "source.pdf",
    "category": "…",
    "situation": "…",
    "url": "https://…",
    "page": 3,
    "source_version": "…",
    "reviewed_at": "ISO-8601"
  }
}
```

ปัจจุบัน PDF chunk ไม่มี `page` และ `chunk_id` ขึ้นกับ counter/ลำดับไฟล์. หากเพิ่ม ingestion ใหม่ ให้รักษา field เดิมและเพิ่ม provenance; อย่าเปลี่ยน `text`, `metadata.situation` เพราะ generator ใช้อยู่.

## 7. สัญญา node 06: Risk knowledge service

Input:

```json
{ "query": "English retrieval query", "top_k": 10, "index_version": "optional" }
```

Output:

```json
{
  "results": [
    { "chunk": { "chunk_id": "…", "text": "…", "metadata": {} }, "rank": 1, "score": 0.82, "retrieval_method": "hybrid+rerank" }
  ],
  "index_version": "…",
  "retrieved_at": "ISO-8601"
}
```

ปัจจุบัน `HybridRetriever.retrieve()` และ `Reranker.rerank()` คืน list ของ chunk โดยไม่มี score/method. Node 07 จึงสร้าง context จาก `chunk['metadata']['situation']` และ `chunk['text']`. หาก refactor ให้รองรับทั้ง wrapper ใหม่และสอง key นี้ในช่วง migration.

Retriever ส่ง evidence เท่านั้น. คะแนน relevance ไม่ใช่คะแนน risk และห้ามตีความ score ต่ำว่า “safe”.

## 8. สัญญา node 07: Decision / LLM engine

Input ที่ generator ต้องได้รับ:

```json
{
  "original_query": "Thai/English user query",
  "history": [{ "role": "user", "content": "…" }],
  "evidence": ["EvidenceChunk"],
  "live_data": ["LiveDataSnapshot"],
  "tool_policy": { "weather": true, "disaster": true, "train": true },
  "language": "th"
}
```

Output:

```json
{
  "reply": "Markdown user-facing answer",
  "safety_level": "unknown | advisory | urgent",
  "used_evidence_ids": ["…"],
  "used_live_sources": ["…"],
  "degraded": false,
  "notices": []
}
```

Guardrails ที่ต้องรักษา:

- ตอบภาษาเดียวกับ query ของผู้ใช้; retrieval query อาจเป็น English ได้
- ใช้เฉพาะ evidence/live snapshot ที่ได้รับ; ไม่มีหลักฐานต้องบอกว่าไม่มีข้อมูลเพียงพอ
- ห้ามแต่ง official warning, train availability, route หรือ emergency instruction
- กรณี distress ต้องยก emergency contacts เฉพาะที่มีใน context
- tool call ต้องอยู่ใน allow-list และ validate arguments; จำนวนรอบ/timeout มีขอบเขต
- คำตอบเป็น Markdown ได้ แต่ไม่ใช่ HTML/JavaScript และไม่พึ่งรูปตาราง

ปัจจุบัน `Generator.generate()` เป็นทั้ง decision layer และ tool executor. เมื่อแยก node ให้ย้าย tool execution ไป node 04/orchestrator และส่ง `LiveDataSnapshot` ให้ generator; contract นี้ทำให้ทดสอบ node 07 แบบไม่เรียกเครือข่ายได้.

## 9. สัญญา node 08: Evaluation และ feedback

Event ขั้นต่ำหลังตอบ:

```json
{
  "request_id": "uuid",
  "timestamp": "ISO-8601",
  "route": "rag",
  "degraded": false,
  "evidence_ids": ["…"],
  "source_versions": ["…"],
  "evaluation_schema_version": "1"
}
```

`golden_set.json` ใช้สำหรับ retrieval evaluation (`expected_chunk_ids`) และ `eval_generation.py` ให้ LLM judge ประเมิน faithfulness/relevance. Feature ใหม่ต้องเพิ่ม test case ใน golden set พร้อม expected chunk ID; ต้องไม่ใช้ข้อความผู้ใช้หรือข้อมูลระบุตัวตนเป็น training data โดยอัตโนมัติ.

## 10. จุดที่ต้องแก้/ระวังก่อนเพิ่ม feature

| ความเสี่ยงปัจจุบัน | ผลกระทบ | Owner ที่ควรรับ |
|---|---|---|
| `global_memory` ไม่แยกผู้ใช้และทับ history ที่ frontend ส่ง | context รั่ว/คำตอบผิดบริบท | 02 + 03 |
| response API มีแค่ `reply` และ error กลับเป็น HTTP 200 | UI/observability แยก failure ไม่ได้ | 02 |
| UI ส่ง toggle ไม่ครบ (`train` หาย) | behavior ต่อ request ไม่ชัด | 01 + 02 |
| train status เป็น mock แต่ wording บอก status | เสี่ยงหลอกว่าเป็นข้อมูลจริง | 04 + 07 |
| live tool output เป็น string ไม่มี source/time/status | audit และ freshness ทำไม่ได้ | 04 |
| evidence PDF ไม่มี page/version | citation ย้อนกลับไม่พอ | 05 + 06 |
| generator ได้ list chunks แต่ไม่คืน evidence trace | node 08 วัด/ตรวจตอบยาก | 06 + 07 + 08 |
| backend CORS เป็น `*` กับ credentials | ไม่เหมาะสำหรับ deploy production | 02 |

## 11. Checklist ให้ AI ประจำ node ก่อนส่ง PR

1. ระบุ node owner และ boundary; ไม่ย้าย business logic ข้าม node โดยไม่แก้ contract
2. ระบุ input/output JSON schema ที่เพิ่มหรือเปลี่ยน และยังรองรับ caller เดิมหรือไม่
3. เพิ่ม validation: required field, enum, max length, timeout, malformed provider/model response
4. มี degraded path ที่คืน `status/notices`, ไม่สร้างความสำเร็จปลอม
5. ส่ง provenance/freshness ต่อไปทุกครั้งที่แตะ evidence หรือ live data
6. อัปเดต golden test/evaluation หากการเปลี่ยนแปลงกระทบ retrieval หรือ answer behavior
7. ทดสอบอย่างน้อย: legacy `message`, canonical `messages`, tool ปิด, provider ล้มเหลว, index ไม่มี/เก่า, Thai query และ English query
8. ห้าม commit `.env`, API key, `vector_db/` ที่ไม่ตั้งใจ หรือ user feedback ที่มีข้อมูลส่วนบุคคล

## 12. ลำดับการเพิ่ม feature ที่ปลอดภัย

1. เขียน/อัปเดต schema และ fixture ก่อน code
2. เปลี่ยน node producer ให้เพิ่ม field ใหม่แบบ optional
3. เปลี่ยน node consumer ให้รองรับทั้ง old/new payload
4. เพิ่ม contract test ข้าม node และ degraded-path test
5. เปิดใช้ behavior ใหม่หลัง observability (`request_id`, route, source status) พร้อม
6. เมื่อ consumer ทั้งหมดย้ายแล้ว จึง deprecate field เดิมใน release ที่ประกาศไว้

เอกสารนี้ตั้งใจให้เป็น baseline: ทุก feature proposal ควรระบุว่าแตะ node ใด, เปลี่ยน contract ใด และรับมือ failure/provenance อย่างไร ก่อนเริ่ม implementation.
