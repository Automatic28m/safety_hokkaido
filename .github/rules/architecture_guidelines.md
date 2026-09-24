# 01_web_app — Implementation Plan

## หน้าที่ของ node

รับผิดชอบ UI, locale, chat presentation และการแสดงผลสถานะจาก backend เท่านั้น ไม่ตัดสิน safety และไม่เก็บ LLM/API key ฝั่ง browser

## สิ่งที่เก็บไว้จากแผนเดิม

- เชื่อม UI กับ API จริง
- เพิ่ม loading และ error state
- เพิ่ม map/PWA ได้ตาม product requirement

## สิ่งที่ต้องเปลี่ยน

- จากรับเฉพาะ `reply` ให้รองรับ `request_id`, `status`, `degraded`, `notices`, `evidence`, `live_sources`
- ส่ง `enabled_agents` ให้ครบ `weather`, `disaster`, `train`
- map ต้องใช้ location data ที่มี provenance ไม่ใช่พิกัดที่ LLM สร้างเอง
- PWA cache ได้เฉพาะคู่มือ static ที่ version ได้; ห้าม cache live warning เป็น current data

## งานที่ต้องทำ

1. ปรับ Next.js proxy ให้ preserve HTTP status และ response fields ทั้งหมดจาก `POST /ask`
2. ปรับ `ChatBot.jsx` ให้ส่ง agent toggle ครบสามตัว
3. เพิ่ม loading, network error, HTTP error, degraded notice และ retry UI
4. แสดง notice, source URL และ fetched time ของข้อมูลสด/evidence อย่างอ่านง่าย
5. render `reply` เป็น sanitized Markdown เท่านั้น
6. เก็บ timestamp เป็น UI-only ไม่ส่งเป็น backend contract
7. หากเพิ่ม map ให้กำหนด schema ของ pin/route พร้อม source URL และ fetched time
8. หากเพิ่ม PWA ให้มี cache version และกลไกล้างคู่มือฉบับเก่า

## กระบวนการทำงานแบบละเอียด

1. ผู้ใช้พิมพ์ข้อความใน `ChatBot` แล้ว UI สร้าง message ใหม่โดยมีเพียง `role: "user"` และ `content`; เวลาแสดงผลเก็บไว้ใน state ของ UI เท่านั้น
2. UI รวมประวัติแชตที่ต้องส่งและ `enabled_agents` ทั้งสามตัว แล้วส่งไป `POST /api/chat` ของ Next.js
3. Next.js proxy ส่ง payload เดิมไป `POST /ask` ของ node 02 โดยไม่ใส่ secret ลง browser และไม่แก้/ตัด field ของ response
4. Proxy รับ HTTP status และ JSON จาก node 02 แล้วส่งต่อทั้ง status และ body ให้ ChatBot หาก response อ่าน JSON ไม่ได้ให้คืน failure state ที่ชัดเจน
5. ChatBot แยกการแสดงผลเป็นสามกรณี: สำเร็จ (`reply`), สำเร็จแบบข้อมูลไม่ครบ (`degraded`/`notices`) และล้มเหลว (HTTP 4xx/5xx หรือ network error)
6. เมื่อสำเร็จ ให้ render `reply` เป็น Markdown; หากมี notices ให้แสดงเป็นกล่องคำเตือนแยกจากเนื้อหาคำตอบ เพื่อไม่ให้ผู้ใช้มองข้าม
7. หาก `live_sources` หรือ `evidence` มีข้อมูล ให้แสดงชื่อแหล่งและเวลาอัปเดตแบบย่อ โดย link ออกไปต้องใช้ URL ที่ backend ส่งมาเท่านั้น
8. หากเพิ่ม map ให้แสดงเฉพาะ pin/route ที่ backend ส่งผ่าน schema ที่กำหนด พร้อม source/time; ถ้าไม่มีข้อมูลพิกัดให้แสดงว่าไม่มีข้อมูลแทนการเดา

## ข้อมูลที่รับและส่ง

- **ส่งไป node 02 ผ่าน proxy:** `message` หรือ `messages`, `enabled_agents`
- **รับกลับ:** `reply`, `request_id`, `status`, `route`, `degraded`, `notices`, `evidence`, `live_sources`
- **รับผิดชอบเฉพาะการแสดงผล:** UI ห้ามแปลผล evidence score หรือสรุป safety เอง

## เกณฑ์รับงาน

- provider ล่มแล้วผู้ใช้เห็น `degraded`/notice
- API error ไม่ถูกแสดงเป็นคำตอบปกติ
- ปิด tool จาก UI แล้ว request ส่งค่า `false` ครบและ backend ไม่เรียก tool นั้น
- response เก่าที่มีแค่ `reply` ยังแสดงได้

## ข้อห้าม

- ห้าม hard-code production backend URL หรือ secret ใน browser
- ห้ามซ่อนสถานะ unavailable/stale/mocked
- ห้ามมี AI watermark หรือ AI contributor ในงานที่ส่งขึ้น GitHub

# 02_api_backend — Implementation Plan

## หน้าที่ของ node

รับผิดชอบ HTTP validation, CORS, health/auth, request/response schema และ error semantics ไม่ใส่ business decision ของ node 03–07 ใน route

## สิ่งที่เก็บไว้จากแผนเดิม

- ยืนยัน API contract
- เชื่อม frontend proxy กับ `POST /ask`
- ทำ logging
- ทำ authentication เมื่อ requirement ด้าน identity ชัดเจน

## สิ่งที่ต้องเปลี่ยน

- แก้ validation/error/CORS ก่อน JWT/OAuth
- ไม่ return error ใน `reply` พร้อม HTTP 200
- ไม่ใช้ mutable default สำหรับ `enabled_agents`

## งานที่ต้องทำ

1. สร้าง Pydantic schema รองรับ legacy `message` และ canonical `messages`
2. validate ว่าต้องมี query, `messages` ไม่ว่าง และรายการสุดท้ายเป็น non-empty `user`
3. รับ role เฉพาะ `user`, `assistant`, `system`, `tool`; แปลง legacy `ai` เป็น `assistant` ที่ boundary
4. สร้าง agent defaults ใหม่ต่อ request; missing key หมายถึง enabled
5. สร้าง `request_id` และส่งต่อไป node 03–08
6. คืน 400 สำหรับ input ผิด, 503 สำหรับ index/pipeline/provider unavailable, 500 สำหรับ unexpected error
7. คืน response ที่คง `reply` และเพิ่ม `status`, `route`, `degraded`, `notices`, `evidence`, `live_sources`
8. จำกัด CORS ด้วย allowed frontend origins; ห้าม `*` กับ credentials
9. log request id, route, status, degraded, latency โดยลดการเก็บ PII
10. หากทำ auth ให้ระบุ user model, token lifecycle และ authorization policy ก่อนเลือก JWT/OAuth

## กระบวนการทำงานแบบละเอียด

1. รับ HTTP request ที่ `/ask` และสร้าง `request_id` ทันทีเพื่อใช้ตามรอย request เดียวกันตลอดระบบ
2. parse body ผ่าน Pydantic schema; ถ้า JSON ไม่ถูกต้อง, ไม่มี query, message สุดท้ายไม่ใช่ user หรือ role ไม่อยู่ใน enum ให้จบที่ HTTP 400 พร้อม `detail`
3. หากพบ legacy role `ai` ให้แปลงเป็น `assistant` ใน object ที่ส่งต่อภายใน โดยไม่แก้ข้อความของผู้ใช้
4. สร้าง `enabled_agents` ใหม่สำหรับ request นี้ โดยตั้ง weather/disaster/train เป็น true ก่อน แล้วนำ explicit false จาก client มาปิดเฉพาะตัวที่ระบุ
5. ประกอบ request object พร้อม request id และส่งให้ node 03; route HTTP ไม่เลือก tool, ไม่ retrieve และไม่เรียก LLM เอง
6. หาก node 03 ส่งผลสำเร็จ ให้ map ผลเป็น response contract โดยคง `reply` และเพิ่ม trace fields ตามที่มี
7. หาก node 03 รายงาน index/provider/pipeline ใช้ไม่ได้ ให้คืน HTTP 503 พร้อม status/degraded/notices ที่ UI อ่านได้
8. หากเกิด exception ที่ไม่คาดคิด ให้ log แบบมี request id และคืน HTTP 500 โดยไม่ส่ง stack trace หรือ secret ไปยังผู้ใช้
9. บันทึก latency, status, route และ degraded เพื่อให้ monitor เห็น error rate โดยไม่จำเป็นต้องบันทึก raw conversation

## ข้อมูลที่รับและส่ง

- **รับจาก node 01:** legacy `message` หรือ canonical `messages` พร้อม optional `enabled_agents`
- **ส่งไป node 03:** request ที่ validate/normalize แล้ว พร้อม `request_id`
- **ส่งกลับ node 01:** HTTP status และ response contract; ไม่ส่ง framework/model object ข้าม boundary

## เกณฑ์รับงาน

- legacy และ canonical payload ผ่าน validation
- HTTP 400/503/500 ถูกต้องตามกรณี
- caller เดิมยังอ่าน `reply` ได้
- CORS ไม่เปิดกว้างเกินจำเป็น

## ข้อห้าม

- ห้ามวาง orchestration, retrieval หรือ LLM decision ใน FastAPI route
- ห้าม commit `.env`/API key หรือ AI watermark/AI contributor

# 03_travel_ai_agent — Implementation Plan

## หน้าที่ของ node

รับผิดชอบ route, context/session orchestration และการเรียก node 04–07 ตาม policy; ไม่สร้างคำตอบ safety เอง

## สิ่งที่เก็บไว้จากแผนเดิม

- ปรับ intent classification
- จัดการ context memory
- ทำ tool routing ให้เชื่อมโมดูลจริง

## สิ่งที่ต้องเปลี่ยน

- ปรับ custom Router/Groq ที่มีอยู่ ไม่ใช่ LangChain
- เปลี่ยน `global_memory` shared process เป็น memory แยกตาม `conversation_id`
- ให้ node 03 เลือก/เรียก tool; node 07 รับผลที่ตรวจแล้ว

## งานที่ต้องทำ

1. สร้าง `OrchestrationRequest`: request id, conversation id, original query, history, enabled agents, locale, received time
2. ให้ history จาก API เป็น authoritative; server memory เป็น cache/summarization ของ conversation เดียวเท่านั้น
3. เลิกใช้ `global_memory` กลางใน production multi-user
4. validate route enum: `general`, `rag`, `realtime`, `rag+realtime`
5. เพิ่ม `fallback_used` ใน RouteDecision และ log ทุก fallback
6. รักษาลำดับ: normalize history → route → reformulate → translate retrieval query → retrieve/rerank → call allowed tools → generate → evaluation event
7. ตรวจ route, `enabled_agents` และ allow-list ก่อนเรียก node 04
8. ส่ง original query, history, evidence, live snapshots, tool policy และ language ให้ node 07

## กระบวนการทำงานแบบละเอียด

1. รับ request ที่ผ่าน validation จาก node 02 และเก็บ `original_query` เป็นข้อความอ้างอิงหลักตลอด request
2. โหลด history ของ `conversation_id` เดียวกันเฉพาะเมื่อ client ไม่ได้ส่ง history ที่ authoritative; ห้ามอ่าน memory ของ session อื่น
3. normalize role/history และส่ง query กับบริบทสั้น ๆ ให้ Router เพื่อคืน `RouteDecision`
4. ตรวจ route ว่าอยู่ใน enum; หาก Router ล้มเหลว ใช้ keyword fallback และตั้ง `fallback_used: true` เพื่อให้ audit ได้
5. หากมี history ให้ reformulate เป็น standalone query สำหรับค้นหา แต่คง original query ไว้สำหรับ node 07 และ audit
6. แปลเฉพาะ retrieval query เป็นภาษาอังกฤษตามที่ retriever รองรับ; ไม่แปลทับข้อความผู้ใช้
7. หาก route มี `rag` ให้เรียก node 06 เพื่อ retrieve/rerank evidence; หากไม่มีให้ส่ง evidence ว่างอย่างชัดเจน
8. หาก route มี `realtime` ให้ตรวจ `enabled_agents` และเรียกเฉพาะ adapter ที่อนุญาตใน node 04; เก็บทุก snapshot แม้เป็น unavailable/stale/mocked
9. ส่ง original query, user-facing history, evidence, live snapshots, language และ tool policy ให้ node 07
10. รับ structured decision กลับมา, append memory เฉพาะ conversation เดียว และส่ง event ที่จำเป็นให้ node 08

## ข้อมูลที่รับและส่ง

- **รับจาก node 02:** request id, conversation id, original query, normalized history, enabled agents
- **เรียก node 04:** validated city/region/line ตาม policy และรับ `LiveDataSnapshot`
- **เรียก node 06:** English retrieval query, top k/index version และรับ evidence wrapper
- **ส่งไป node 07:** evidence/live data ที่ได้จริง พร้อม language/tool policy
- **ส่งไป node 08:** request trace หลังตอบ; ไม่ส่ง business decision ไปแก้ feedback

## เกณฑ์รับงาน

- history ของสอง conversation ไม่ข้ามกัน
- API history ไม่ถูก server global state ทับ
- route/fallback trace ได้
- tool ที่ caller ปิดไม่ถูกเรียก

## ข้อห้าม

- ห้ามใช้ route หรือ relevance score ตัดสินว่า safe
- ห้ามให้ generator เรียก provider โดยตรง
- ห้ามมี AI watermark หรือ AI contributor ในงานที่ส่งขึ้น GitHub

# 04_external_data_services — Implementation Plan

## หน้าที่ของ node

รับผิดชอบ provider adapters, input validation, timeout, cache และ live-data normalization; ไม่ตัดสิน safety หรือสร้างคำตอบผู้ใช้

## สิ่งที่เก็บไว้จากแผนเดิม

- แทน mock ด้วยข้อมูลจริง
- ทำ adapter สถานะ JR Hokkaido
- ใช้ caching ลด provider calls

## สิ่งที่ต้องเปลี่ยน

- ทุก provider คืน `LiveDataSnapshot` แทน string
- train adapter ปัจจุบันต้องระบุ `mocked`
- ก่อนทำ JR scraping ต้องตรวจ official source, ข้อตกลงการใช้ และความเสถียรก่อน

## งานที่ต้องทำ

1. ปรับ weather, disaster และ train ให้คืน provider, kind, scope, status, fetched at, expires at, data, source URL, error code
2. ใส่ timeout, input validation และ malformed-response handling ทุก adapter
3. คืน `unavailable` เมื่อ provider ล้มเหลว; ห้ามตอบ “No warnings” จาก error
4. แยก JMA data ที่ fetch จริงออกจาก hardcoded snow statement
5. ให้ train simulation คืน `status: mocked` จนกว่าจะมี verified JR adapter
6. ทำ cache ที่มี TTL; cache ต้องไม่ลบ/บัง fetched time และ source URL
7. จำกัด input scope ตาม adapter เช่น city/region/line ที่ validate แล้ว

## กระบวนการทำงานแบบละเอียด

1. รับ argument ที่ node 03 validate มา เช่น city, region หรือ line name; adapter ไม่รับ object ของ LLM โดยตรง
2. ตรวจรูปแบบและขอบเขตของ argument ก่อนสร้าง provider request เพื่อป้องกัน request ผิดหรือเกิน scope
3. ตรวจ cache ด้วย provider/kind/scope; หาก cache ยังไม่หมดอายุ ให้คืน snapshot เดิมพร้อม fetched/expiry time จริง
4. หากต้องเรียก provider ให้ใช้ timeout ที่กำหนด และ parse response ตาม schema ของ provider นั้น
5. normalize หน่วย/ชื่อพื้นที่/ข้อมูลสำคัญเป็น fieldใน `data` แต่ไม่สรุปว่าปลอดภัยหรือไม่
6. เมื่อสำเร็จให้สร้าง snapshot `ok` พร้อม provider, source URL, fetched at และ expires at แล้วเก็บ cache ตาม TTL
7. เมื่อ provider ตอบไม่ครบ ให้คืน `partial`; เมื่อข้อมูลเก่ากว่า TTL ให้คืน `stale`; เมื่อเชื่อมต่อไม่ได้/timeout ให้คืน `unavailable`
8. สำหรับ train simulation ปัจจุบัน ให้คืน `mocked` แม้ข้อความจำลองจะมีรายละเอียด และส่ง notice เพื่อไม่ให้ caller นำเสนอเป็น live source
9. ส่ง snapshot กลับ node 03 ทุกกรณี ไม่ throw ข้อความ string ที่บังคับให้ caller เดา error เอง

## ข้อมูลที่รับและส่ง

- **รับจาก node 03:** validated primitive input และ request context ที่จำเป็น
- **ส่งกลับ node 03:** `LiveDataSnapshot` พร้อม status/source/time/error code
- **ไม่ส่ง:** recommendation, safety level หรือข้อความ user-facing final answer

## เกณฑ์รับงาน

- ทุก adapter คืน schema เดียวกัน
- timeout/provider failure เป็น `unavailable` พร้อม notice ที่อธิบายได้
- data เก่าระบุ `stale`; mock ระบุ `mocked`
- node 07 ไม่ได้รับ string live data แบบไม่มี provenance

## ข้อห้าม

- ห้ามอ้าง mock ว่า live
- ห้าม fabricate success จาก provider failure
- ห้ามมี AI watermark หรือ AI contributor ในงานที่ส่งขึ้น GitHub

# 05_data_integration — Implementation Plan

## หน้าที่ของ node

รับผิดชอบ corpus ingestion, cleaning, chunking, embedding และการ build index; ไม่ดึง live data และไม่สร้างคำตอบ safety

## สิ่งที่เก็บไว้จากแผนเดิม

- ซ่อม pipeline ให้รองรับ malformed/null data
- จัดรูปแบบข้อมูลเพื่อใช้กับ AI

## สิ่งที่ต้องเปลี่ยน

- ใช้ FAISS + BM25 + chunk store ตามโค้ดจริง ไม่ใช่ Chroma/Pinecone
- ส่ง evidence structured object ไม่รวม live data เป็นข้อความก้อนเดียว
- เพิ่ม stable ID และ provenance ของ PDF/document

## งานที่ต้องทำ

1. เพิ่ม `page` ให้ PDF chunk และรักษา `text`/`metadata.situation` เพื่อ compatibility
2. สร้าง stable chunk ID ที่ไม่ขึ้นกับ file counter หรือ glob order
3. เพิ่ม `source_version`, `reviewed_at`, source file, category, situation และ URL ใน metadata
4. ยังคง exclude `golden_set.json` จาก ingestion
5. สร้าง `document.index`, `bm25_index.pkl`, `chunk_store.json`, `index_meta.json` เป็นชุดเดียว
6. เพิ่ม manifest: corpus hash, embedding model, chunk settings, build time, schema version
7. handle invalid JSON, PDF extract failure และ null field โดยไม่สร้าง index ที่ไม่สมบูรณ์

## กระบวนการทำงานแบบละเอียด

1. เริ่ม build จากรายการ corpus ที่ review แล้วใน `data/`; ข้าม `golden_set.json` เพราะใช้ประเมิน ไม่ใช่ความรู้ให้ AI
2. อ่าน JSON/TXT/PDF ทีละไฟล์และตรวจ parse/extract; ถ้าไฟล์เสียให้รายงานชื่อไฟล์และหยุด/mark build failed ตาม policy แทนการทำ index เงียบ ๆ
3. สำหรับ PDF ให้แยกข้อความตามหน้า เพื่อผูก chunk ที่สร้างกับเลขหน้าต้นทางได้
4. ทำความสะอาดข้อความและ chunk ด้วย parameters ที่ประกาศไว้ จากนั้นสร้าง stable chunk id จากข้อมูลต้นทางที่คงที่
5. ใส่ metadata เช่น source file, URL, category, situation, page, source version และ reviewed at ให้ทุก chunk
6. สร้าง embeddings แล้ว build FAISS index, BM25 index และ canonical chunk store จากชุด chunks เดียวกัน
7. เขียน artifacts ไปยังพื้นที่ชั่วคราว พร้อม index manifest ที่เก็บ corpus hash/model/chunk config/build time/schema version
8. ตรวจว่า artifacts ครบและ version ตรงกันก่อน publish สลับเป็นชุดใหม่; หากขั้นใดล้มเหลวให้คงชุดเก่าไว้

## ข้อมูลที่รับและส่ง

- **รับ:** corpus ที่ผ่าน review และ build configuration
- **ส่งให้ node 06 ผ่าน storage contract:** FAISS, BM25, chunk store และ index manifest ที่ version ตรงกัน
- **ไม่รับผิดชอบ:** live provider data, route decision หรือ final answer

## เกณฑ์รับงาน

- PDF evidence มี page หากอ่านได้
- index artifacts ทั้งหมดมี version เดียวกัน
- build failure ไม่ทิ้ง artifact ผสมรุ่น
- แหล่งใหม่ผ่าน review ก่อน ingest

## ข้อห้าม

- ห้ามเอาเว็บที่ยังไม่ review เข้า corpus
- ห้ามเปลี่ยน field เดิมของ chunk จน generator/consumer เก่าพัง
- ห้ามมี AI watermark หรือ AI contributor ในงานที่ส่งขึ้น GitHub

# 06_risk_knowledge_services — Implementation Plan

## หน้าที่ของ node

รับผิดชอบ retrieve/rerank evidence พร้อม rank, score และ provenance; ไม่ตัดสินว่า safe/unsafe และไม่สร้างคำตอบผู้ใช้

## สิ่งที่เก็บไว้จากแผนเดิม

- ทดสอบความแม่นยำของ RAG
- ใช้คู่มือภัยพิบัติใน vector index

## สิ่งที่ต้องเปลี่ยน

- ไม่ทำ task ปรับ local ML risk model เพราะโค้ดปัจจุบันไม่พบโมเดลดังกล่าว
- ใช้ FAISS/BM25 ที่มีอยู่จริง
- แยก retrieval relevance score ออกจาก risk level

## งานที่ต้องทำ

1. ให้ `HybridRetriever.retrieve()` คืน `results`, `index_version`, `retrieved_at`
2. ให้ result แต่ละรายการมี `chunk`, `rank`, `score`, `retrieval_method`
3. ให้ reranker รักษา evidence metadata เดิมและเพิ่ม rerank method/score ตามจำเป็น
4. รองรับ output list แบบเดิมในช่วง migration
5. เพิ่ม golden-set case พร้อม expected chunk IDs เมื่อเปลี่ยน retrieval/corpus
6. ตรวจ index version ที่ caller ขอ และตอบ error/degraded เมื่อ index ใช้ไม่ได้

## กระบวนการทำงานแบบละเอียด

1. รับ English retrieval query, `top_k` และ optional index version จาก node 03
2. โหลด FAISS/BM25/chunk store/manifest เป็นชุดเดียว; หาก artifact ขาดหรือ version ไม่ตรงให้รายงาน unavailable แทนคืนผลมั่ว
3. encode query แล้วค้นหา dense candidates จาก FAISS
4. ทำ BM25 search สำหรับ lexical candidates และรวมผลด้วย hybrid method ที่กำหนด
5. จัดอันดับ candidate แล้วส่งให้ reranker เมื่อเปิดใช้; reranker ต้องคืนข้อมูล chunk เดิมพร้อม score/method ที่ trace ได้
6. สร้าง result wrapper โดยใส่ chunk, rank, score, retrieval method, index version และ retrieved time
7. ส่ง evidence ให้ node 03 โดยไม่เติมคำแนะนำ, warning หรือ safety judgement
8. ใช้ golden set วัดว่า expected chunk IDs ถูกค้นเจอหลังมีการเปลี่ยน corpus/model/algorithm

## ข้อมูลที่รับและส่ง

- **รับจาก node 03:** English query, top k, optional index version
- **อ่านจาก node 05:** index artifacts/manifest ที่ build เสร็จแล้ว
- **ส่งกลับ node 03:** ranked evidence wrapper เท่านั้น

## เกณฑ์รับงาน

- node 07 ได้ evidence พร้อม source/time/rank/method
- retrieval score ไม่ถูกใช้ตัดสิน safety
- evaluation วัด hit rate/MRR กับ golden set ได้

## ข้อห้าม

- ห้ามสร้างหรือสรุป official warning เอง
- ห้ามนำ relevance score ต่ำไปพูดว่า “ปลอดภัย”
- ห้ามมี AI watermark หรือ AI contributor ในงานที่ส่งขึ้น GitHub

# 07_decision_llm_engine — Implementation Plan

## หน้าที่ของ node

รับ evidence และ live snapshots ที่ผ่านการตรวจแล้วมาสร้างคำตอบ grounded พร้อม guardrails; ไม่เรียก provider/network tool เอง

## สิ่งที่เก็บไว้จากแผนเดิม

- ลด hallucination ด้วย system prompt/guardrail
- ตอบภาษาตามผู้ใช้ และจริงจังเมื่อฉุกเฉิน
- ตั้งค่า LLM provider/API key ฝั่ง server

## สิ่งที่ต้องเปลี่ยน

- โค้ดจริงใช้ Groq จึงไม่ assume ว่าต้องเป็น Gemini/OpenAI
- ย้าย tool call loop ออกจาก generator ไป node 03/04
- generator คืน structured decision; backend เป็นผู้ประกอบ HTTP response

## งานที่ต้องทำ

1. เปลี่ยน input เป็น original query, history, evidence, live data, tool policy, language
2. ลบ provider tool execution/tool schemas ออกจาก generator
3. ปรับ prompt ให้ใช้เฉพาะ evidence/live snapshot ที่ได้รับ
4. ถ้าข้อมูลไม่พอหรือ dependency unavailable ให้บอกข้อจำกัด ไม่สรุป safe
5. ห้ามแต่ง official warning, train availability, travel route หรือ emergency instruction
6. ให้ emergency contact ปรากฏเฉพาะเมื่อมีอยู่ใน context
7. คืน `reply`, `safety_level`, `used_evidence_ids`, `used_live_sources`, `degraded`, `notices`
8. จำกัด output เป็น Markdown ไม่มี HTML/JavaScript และไม่พึ่งตาราง

## กระบวนการทำงานแบบละเอียด

1. รับ original query, user-visible history, evidence, live snapshots, language และ tool policy จาก node 03
2. ตรวจว่าหลักฐาน/live data ทุกชิ้นมี source/status/time ที่จำเป็น; ถ้าบาง dependency unavailable ให้เตรียม notice ไม่ปกปิด
3. แปลง evidence และ snapshot ที่ได้รับเป็น context สำหรับ model โดยเก็บ evidence id/source mapping ไว้แยกจากข้อความ prompt
4. สร้าง system prompt ที่กำหนดให้ตอบภาษาของผู้ใช้, ใช้เฉพาะ context และไม่แต่ง official facts หรือ emergency instructions
5. เรียก LLM provider ที่ server ตั้งค่าไว้โดยไม่มี tool schema/network tool ให้ model execute
6. ตรวจ output ว่าเป็น Markdown text ปลอดภัย ไม่มี HTML/JavaScript และไม่อ้าง source ที่ไม่ได้รับ
7. สร้าง structured decision: reply, safety level, used evidence IDs, used live sources, degraded และ notices
8. หาก model/provider ล้มเหลว ให้คืน failure/degraded result ที่ node 02 map เป็น HTTP semantics; ไม่สร้าง reply ที่เลียนแบบคำตอบจริง

## ข้อมูลที่รับและส่ง

- **รับจาก node 03:** query/history/evidence/live data/tool policy/language ที่ผ่าน validation แล้ว
- **ส่งกลับ node 03:** structured decision เท่านั้น
- **ไม่ทำ:** เลือก tool, เรียก weather/JMA/JR, แก้ index หรือเขียน feedback

## เกณฑ์รับงาน

- generator unit test ใช้ fixture ได้โดยไม่มี network call
- unavailable/stale/mocked source ถูกสะท้อนเป็น notice
- Thai query ตอบไทย และ English query ตอบอังกฤษ
- evidence IDs ใน output อ้างถึงหลักฐานที่ได้รับจริง

## ข้อห้าม

- ห้ามเรียก external provider เอง
- ห้ามสร้าง warning/route/fact ที่ไม่มีใน input
- ห้ามมี AI watermark หรือ AI contributor ในงานที่ส่งขึ้น GitHub

# 08_recommendation_feedback — Implementation Plan

## หน้าที่ของ node

รับผิดชอบ evaluation, audit event และ optional feedback; ไม่เปลี่ยน safety behavior อัตโนมัติและไม่เป็นส่วนตัดสินคำตอบฉุกเฉิน

## สิ่งที่เก็บไว้จากแผนเดิม

- มี schema ที่ UI ใช้งานได้แน่นอน
- เปิด feedback API สำหรับ thumbs up/down

## สิ่งที่ต้องเปลี่ยน

- response schema หลักเป็นงานร่วม 02/07; node 08 บันทึก audit/evaluation ของ response
- feedback เป็น optional และ privacy-minimized
- ห้าม auto-train หรือ auto-change guardrail จาก feedback

## งานที่ต้องทำ

1. บันทึก event หลังตอบ: request id, timestamp, route, degraded, evidence IDs, source versions, evaluation schema version
2. สร้าง feedback API เก็บ signal ที่จำเป็นและแยกจาก raw query/PII
3. เชื่อม thumbs up/down จาก UI เมื่อ endpoint พร้อม
4. รักษา/เพิ่ม `golden_set.json` สำหรับ retrieval evaluation
5. รัน retrieval และ generation evaluation เมื่อ retrieval/prompt/answer behavior เปลี่ยน
6. บังคับ human review ก่อนเปลี่ยน safety rule, prompt หรือ model policy จาก feedback/evaluation

## กระบวนการทำงานแบบละเอียด

1. หลัง node 03/07 สร้างคำตอบเสร็จ รับ event ที่มี request id, timestamp, route, degraded, evidence IDs และ source/index versions
2. validate event schema และบันทึก audit record โดยลด/ไม่เก็บ raw query หรือข้อมูลระบุตัวบุคคลตาม retention policy
3. หาก UI ส่ง thumbs up/down ให้เก็บเป็น optional feedback signal ที่ผูกกับ request id เท่าที่จำเป็น ไม่ปะปนกับ safety decision runtime
4. สำหรับ retrieval evaluation ให้อ่าน `golden_set.json`, เรียก node 06 และวัด hit rate/MRR จาก expected chunk IDs
5. สำหรับ generation evaluation ใช้ fixture/evidence ที่ควบคุมได้เพื่อวัด faithfulness/relevance โดยไม่ให้ judge เปลี่ยน production prompt เอง
6. รายงาน regression ให้ทีมมนุษย์ตัดสินว่าควรแก้ corpus, retrieval, prompt หรือ UI; feedback ไม่มีสิทธิ์ปรับ guardrail อัตโนมัติ
7. เก็บ evaluation schema version กับ event เพื่อเปรียบเทียบผลข้าม release ได้

## ข้อมูลที่รับและส่ง

- **รับจาก node 03/07:** trace/evaluation event หลังตอบ ไม่ใช่ model/database connection
- **รับจาก node 01:** optional feedback signal ที่ privacy-minimized
- **ส่งกลับ:** report/metric/audit record; ไม่ส่งคำสั่งเปลี่ยน safety behavior กลับ runtime อัตโนมัติ

## เกณฑ์รับงาน

- ทุกคำตอบมี audit event ที่ trace evidence/source version ได้
- feedback ไม่มีผลต่อ guardrail โดยอัตโนมัติ
- evaluation regressions ถูกตรวจพบก่อน release

## ข้อห้าม

- ห้ามใช้ feedback เป็น training data โดยอัตโนมัติ
- ห้ามเก็บ PII หรือ raw query เกินความจำเป็น
- ห้ามมี AI watermark หรือ AI contributor ในงานที่ส่งขึ้น GitHub
