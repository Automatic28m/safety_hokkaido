# 📌 สรุปรายงานการพัฒนา: 06_risk_knowledge_services (Safety Hokkaido)
**เอกสารสรุปผลการดำเนินงาน, ปัญหาที่พบ, การแก้ไข, และการเชื่อมต่อระบบ RAG**

---

## 🎯 1. สิ่งที่พัฒนาและปรับปรุงทั้งหมด (What Was Done)

เพื่อให้สอดคล้องกับข้อกำหนดใน `SAFETY_HOKKAIDO_NODE_CONTRACT.md` และต่อท่อข้อมูลกับโมดูล `05_data_integration` และ `07_decision_llm_engine` ได้อย่างสมบูรณ์ โมดูล `06_risk_knowledge_services` ได้รับการพัฒนาในประเด็นสำคัญดังนี้:

### 1.1 สร้าง Data Schemas มาตรฐานด้วย Pydantic v2 (`models.py`)
* สร้างคลาสโครงสร้างข้อมูลตามสัญญา:
  * `EvidenceChunk` & `EvidenceChunkMetadata`: รองรับการเก็บเลขหน้าเอกสาร (`page`, `page_number`), ที่มาของไฟล์ (`source_file`), ลิงก์อ้างอิง (`url`), และแฮชเวอร์ชัน (`source_version`)
  * `RetrievalResultItem`: โครงสร้างผลลัพธ์แต่ละอันดับ ระบุ `rank`, `score` (คะแนนความแม่นยำ), และ `retrieval_method`
  * `RiskAssessment`: ผลการประเมินความเสี่ยง มีระดับ `RiskLevel` (`LOW`, `MEDIUM`, `HIGH`, `UNKNOWN`), คะแนน `risk_score` (0.0–1.0), และปัจจัยความเสี่ยง `primary_factors`
  * `RouteInfo`: โครงสร้างข้อมูลเส้นทางหลัก ทางเลี่ยง และจุดปิดกั้น (`closed_segments`)
  * `RiskKnowledgeResponse`: ก้อนข้อมูลรวมตาม Contract พร้อมฟิลด์ `degraded` และ `notices`

### 1.2 ยกระดับ Hybrid Retriever (`hybrid_retriever.py`)
* **Two-Stage Hybrid Search:** ค้นหาความหมายด้วย Dense FAISS ควบคู่กับคำศัพท์เฉพาะทางด้วย Sparse BM25 และผสานผลด้วย Reciprocal Rank Fusion (RRF, $k=60$)
* **รักษา Page Provenance:** ดึงข้อมูลเลขหน้าจาก Chunk Store ของโมดูล 05 มาแม็ปเข้า `EvidenceChunk` อย่างถูกต้อง 100%
* **ระบบความปลอดภัยและการกู้คืน (Graceful Degradation):**
  * หากไฟล์ Index ไม่อยู่หรือไม่พร้อมใช้งาน ระบบจะไม่แครช แต่จะตั้งค่า `degraded: true` พร้อมบันทึกข้อความแจ้งเตือน (`notices`) ตามกฎ Fail Conservatively
* **Backward Compatibility 100%:**
  * แม้จะคืนค่าเป็น Model วัตถุใหม่ แต่รองรับการเข้าถึงแบบดั้งเดิม `chunk['text']` และ `chunk['metadata']['situation']` ทำให้โค้ดของ `pipeline.py` (โมดูล 03) และ `generator.py` (โมดูล 07) ทำงานได้ทันทีโดยไม่ต้องแก้ไข

### 1.3 ยกระดับ Cross-Encoder Re-ranker (`rerankers.py`)
* บันทึกคะแนนความเกี่ยวข้องที่แท้จริง (`score`) และอันดับ (`rank`) ลงในออบเจกต์ผลลัพธ์
* มีระบบ Lazy Loading และ Fallback อัตโนมัติ หากไม่สามารถโหลดโมเดล Cross-Encoder ได้ จะส่งคืนผลลัพธ์แบบ Hybrid ดั้งเดิมโดยไม่หยุดการทำงานของระบบ

### 1.4 ปรับปรุงเอกสารสัญญาระบบ (`01_env.md`, `02_step.md`, `03_process.md`)
* อัปเดตข้อกำหนดทางสถาปัตยกรรม กฎความปลอดภัย ห้ามฟันธงการกระทำแทนผู้ใช้ และข้อห้ามเรื่องลายน้ำ AI

### 1.5 พัฒนา Local Risk Model Engine (`risk_model.py`)
* **Multi-Factor Risk Scoring:**
  * คำนวณคะแนนความเสี่ยงถ่วงน้ำหนัก ($S_{\text{risk}} = 0.45 \times S_{\text{disaster}} + 0.35 \times S_{\text{weather}} + 0.20 \times S_{\text{transit}}$)
  * **Disaster Sub-model:** วิเคราะห์ระดับแรงสั่นสะเทือนแผ่นดินไหว JMA Shindo (สเกล 1 ถึง 7, 5弱/5強, 6弱/6強) และประกาศเตือนภัยฉุกเฉิน (Tsunami, Blizzard Warning, Heavy Snow Warning, Landslide)
  * **Weather Sub-model:** ประเมินความเร็วลม (เกณฑ์พายุหิมะ Whiteout $\ge 20\text{ m/s}$), ปริมาณหิมะตกสะสม, อุณหภูมิหนาวจัด ($\le -15^\circ\text{C}$ เสี่ยง Hypothermia)
  * **Transit Sub-model:** ตรวจสอบสถานะสายรถไฟ JR และโครงข่ายถนน (Suspended, Delayed, Normal) พร้อมระบุจุดปิดกั้นเส้นทาง (`closed_segments`)
* **Fail-Safe Emergency Override:**
  * หากเกิดเหตุวิกฤต เช่น สึนามิ, แผ่นดินไหวรุนแรง Shindo $\ge 5$, หรือพายุหิมะ Whiteout ลมแรง ระบบจะรับประกันระดับความเสี่ยงขั้นต่ำที่ `HIGH` ($\ge 0.70$) ทันที ไม่ถูกเฉลี่ยลดทอนลง
* **Fail Conservatively & Dynamic Re-weighting:**
  * หาก Data Feed บางส่วนขาดหาย จะคำนวณและปรับสัดส่วนน้ำหนักใหม่เฉพาะ Feed ที่ใช้งานได้ พร้อมแนบ Notice แจ้งเตือนอย่างโปร่งใส
  * หาก Data Feeds ทั้งหมดใช้งานไม่ได้ จะคืนค่า `RiskLevel.UNKNOWN` พร้อมแจ้งเตือนความปลอดภัยทันที
* **Route Evaluation (`RouteInfo`):**
  * คัดกรองและแนะนำเส้นทางปลอดภัย (`recommended_route`), เส้นทางเลี่ยงสำรอง (`alternative_routes`), และบันทึกจุดที่ถูกระงับ/ปิดกั้น (`closed_segments`)

### 1.7 สร้าง Unified Service Facade และ In-Memory Caching (`risk_service.py`)
* **Single Entrypoint Architecture:**
  * รวม `HybridRetriever`, `Reranker`, และ `LocalRiskModel` เข้าด้วยกันเป็น Facade คลาสเดียว `RiskKnowledgeService`
  * เมธอด `get_risk_knowledge(...)`: ประมวลผลทั้งการสืบค้นเอกสาร RAG และการวิเคราะห์ความเสี่ยง พร้อมส่งกลับเป็นโมเดล `RiskKnowledgeResponse` ที่สมบูรณ์ในคำสั่งเดียว
  * เมธอด `retrieve_evidence(...)`: ค้นหาเฉพาะเอกสารความปลอดภัยสำหรับคำถามทั่วไป
  * เมธอด `assess_risk(...)`: ประเมินเฉพาะความเสี่ยงเส้นทางแบบเรียลไทม์
  * การรวมข้อความแจ้งเตือน (`notices`) และการตั้งค่าสถานะ `degraded: true` อย่างเป็นระบบ

### 1.8 การทำนายแนวโน้มความเสี่ยงล่วงหน้า (Temporal Hazard Trend Forecasting)
* เพิ่ม Enum `RiskTrend` (`STABLE`, `DETERIORATING`, `IMPROVING`) ใน `models.py`
* พัฒนาเมธอด `evaluate_forecast_trend()` ใน `risk_model.py` ตรวจจับแนวโน้มพยากรณ์อากาศล่วงหน้า 12-24 ชั่วโมง:
  * คาดการณ์จุดเสี่ยงสูงสุด (`forecasted_peak_score`) และกรอบเวลาวิกฤต (`forecasted_peak_window`)
  * หากพยากรณ์พบว่าความเร็วลมหรือหิมะจะทวีความรุนแรงขึ้น $\ge 0.20$ หรือแตะระดับวิกฤต $\ge 0.70$ ระบบจะแจ้งเตือน `RiskTrend.DETERIORATING` ทันที เพื่อให้นักท่องเที่ยวเตรียมพร้อมก่อนเกิดเหตุ

### 1.9 การประเมินความเสี่ยงเชิงภูมิศาสตร์และช่องเขา (Geo-Spatial & Corridor Hazard Multipliers)
* พัฒนาเมธอด `evaluate_corridor_risk()` ใน `risk_model.py`
* ตรวจจับเส้นทางสัญจรที่ตัดผ่านช่องเขาสูงชันและเสี่ยงอันตรายในฮอกไกโด:
  * ช่องเขา Nakayama Pass (Route 230), Nissho Pass (Route 274), Mikuni Pass (Route 273), Sekihoku Pass (Route 39), Karikachi Pass (Route 38)
  * ชายฝั่งลมกรรโชกแรงเสี่ยงไวท์เอาต์ (Otaru-Yoichi coastal strip, Rumoi, Soya/Wakkanai)
* บังคับใช้ Elevation / Coastal Hazard Multipliers (ตัวคูณความเสี่ยง $\times 1.25$ ถึง $\times 1.35$) เมื่อสภาพอากาศเข้าข่ายอันตราย

### 1.10 การจัดลำดับความสำคัญของเอกสารฉุกเฉินแบบปรับตัว (Adaptive Emergency Retrieval)
* ระบบตรวจสอบ intent ของคำค้นหาฉุกเฉิน (เช่น ติดในรถ, หิมะถล่ม, ไวท์เอาต์, SOS, โทร 119/110, อุณหภูมิต่ำวิกฤต) หรือสภาวะที่มี `RiskLevel.HIGH`
* สลับนำ chunk เอกสารหมวดกู้ภัยและเอาชีวิตรอด (`emergency`, `whiteout`, `firstaid`, `survival`) ขึ้นสู่อันดับ 1 โดยอัตโนมัติ เหนือเอกสารท่องเที่ยวทั่วไป

### 1.11 แคชความเร็วสูงในหน่วยความจำ (Sub-10ms High-Performance In-Memory Cache)
* ทำ Hashing กุญแจแคชด้วย SHA-256 จาก `query`, `top_k`, และ Live Snapshots (Weather, Disaster, Transit, Route Context)
* กำหนดค่า TTL หมดอายุอัตโนมัติ (Default 90 วินาที)
* มอบความเร็วในการตอบสนองคำสั่งซ้ำต่ำกว่า 10 มิลลิวินาที (<10ms) พร้อมฟังก์ชัน `get_cache_stats()` และ `clear_cache()`

### 1.12 ชุดทดสอบจำลองวิกฤตประวัติศาสตร์ฮอกไกโด (Hokkaido Landmark Crisis Benchmark Suite)
* สร้าง `tests/test_crisis_benchmarks.py` จำลองเหตุการณ์จริงระดับประวัติศาสตร์:
  1. **2022 Sapporo Whiteout Blizzard:** ลมกระโชกแรง $25.8\text{ m/s}$ หิมะท่วมขัง รถไฟสายหลักหยุดให้บริการ
  2. **2018 Eastern Iburi Mega-Earthquake:** แผ่นดินไหวรุนแรง Shindo 7, ขนาด 6.7, ไฟฟ้าดับทั่วเกาะ (Blackout)
  3. **Nakayama Mountain Pass Multiplier:** ทดสอบตัวคูณความเสี่ยงช่องเขาหิมะหนา
  4. **Hourly Forecast Deteriorating Trajectory:** ทดสอบการตรวจจับพายุล่วงหน้า
  5. **Performance Cache Hit & Latency:** ทดสอบแคชตอบกลับไวกว่า 10ms
  6. **Adaptive Emergency Prioritization:** ทดสอบการดันเอกสาร 119/เอาชีวิตรอดขึ้นอันดับแรก

---

## ⚠️ 2. ปัญหาที่พบระหว่างทางและวิธีแก้ไข (Problems & Solutions)

| ปัญหาที่พบ | สาเหตุ | วิธีการแก้ไข |
|---|---|---|
| **1. เลขหน้าและที่มาตกหล่น** | โค้ดเดิมไม่สกัดฟิลด์ `page` และ `source_version` จาก Chunk Store | ดึงฟิลด์ `page`/`page_number` จาก metadata มาแม็ปเข้า `EvidenceChunkMetadata` |
| **2. ความเสี่ยงแครชเมื่อขาด Index** | ถ้าไฟล์ `document.index` หรือ `bm25_index.pkl` ไม่มีอยู่ โค้ดเดิมจะ Exception ล่มทันที | ดักจับ Exception ใน `_load_indices()` และคืนสถานะ `degraded=True` อย่างปลอดภัย |
| **3. บั๊ก Dictionary Subscript** | โค้ดภายนอก (Node 03/07) เรียก `c['text']` และ `c['metadata']` ซึ่ง Pydantic ปกติไม่รองรับ | เพิ่มเมธอด `__getitem__`, `__contains__`, และ `get()` ใน Model ให้ทำหน้าที่เป็น Transparent Proxy |
| **4. ผลการจัดอันดับไม่มี Score** | โค้ดเดิมตัด score ทิ้งหลังจาก sort เหลือแค่ chunk ดิบ | คงค่า `score` และ `rank` ไว้ใน `RetrievalResultItem` เพื่อใช้วิเคราะห์และตรวจสอบย้อนหลัง |
| **5. Cross-module Dependency ในการทดสอบ** | การทดสอบกับโมเดล `LiveDataSnapshot` ของโมดูล 04 เรียกหา `config` และ `requests` | จัดการโครงสร้าง `sys.path` ให้รองรับทั้งการรันเดี่ยวและการรันแบบ Cross-Module อย่างสมบูรณ์ |
| **6. ความซ้ำซ้อนในการเรียกใช้โมดูล 06** | โมดูลภายนอก (03/07) ต้องประกอบ Retriever, Reranker และ RiskModel แยกกัน | สร้าง `RiskKnowledgeService` เป็น Facade จุดเดียว ลดความซ้ำซ้อนและรับประกัน Response Schema |
| **7. ข้อจำกัดคะแนนวิกฤตในแผ่นดินไหวขนาดใหญ่** | แผ่นดินไหว Shindo 7 เมื่อรวมถ่วงน้ำหนักกับวันที่อากาศแจ่มใส คะแนนถูกเกลี่ยเหลือ 0.75 | ปรับปรุง Fail-Safe Override: หาก $S_{\text{disaster}} \ge 0.90$ บังคับคะแนน $\ge 0.90$ ทันที |
| **8. Re-ranker Output Type Inconsistency** | เมื่อ Cross-Encoder จัดอันดับคืนค่า EvidenceChunk ดิบ ทำให้ขาด rank/score item wrapper | Wrap `EvidenceChunk` เป็น `RetrievalResultItem` เสมอใน `rerankers.py` |

---

## 📊 3. ผลการทดสอบอัตโนมัติ (Automated Test Results)

```bash
Ran 34 tests in 62.418s

OK
```
* `test_models.py` (8 Tests) — ผ่าน 100%
* `test_hybrid_retriever.py` (4 Tests) — ผ่าน 100%
* `test_rerankers.py` (3 Tests) — ผ่าน 100%
* `test_risk_model.py` (8 Tests) — ผ่าน 100%
* `test_risk_service.py` (5 Tests) — ผ่าน 100%
* `test_crisis_benchmarks.py` (6 Tests) — ผ่าน 100%

**รวมทั้งสิ้น 34 จาก 34 Tests ผ่านเรียบร้อยสมบูรณ์ (100% Pass Rate)**
