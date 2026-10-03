# 📋 สรุปภาพรวมระบบและการแก้ไขปัญหา โมดูล 04: External Data Services
**ระบบ Safety Hokkaido — ข้อมูลระบบ, ฟังก์ชันการทำงาน, ปัญหาที่พบระหว่างพัฒนา และแนวทางแก้ไข**

---

## 🎯 1. ระบบของเรามีอะไรบ้าง (System Overview & Components)

โมดูล **04: External Data Services** ทำหน้าที่เป็น **Single Source of Truth** ในการเชื่อมต่อ, รวบรวม, และจัดระเบียบข้อมูลสภาวะแวดล้อมจริงแบบเรียลไทม์ (Live Real-Time Data) ในภูมิภาคฮอกไกโด เพื่อส่งมอบเป็นหลักฐานเชิงประจักษ์ (Normalized Evidence) ให้แก่:
- **Node 06 (Risk Knowledge Services):** ใช้คำนวณคะแนนความเสี่ยงเฉพาะพื้นที่ (`LocalRiskModel`)
- **Node 03 (Travel AI Agent):** ใช้เรียกผ่าน Function Calling Tool เพื่อประกอบการตอบคำถามผู้ใช้งาน
- **Node 07 (Decision LLM Engine):** ใช้ตรวจสอบ Guardrails และตัดสินใจแนะนำแผนการเดินทางที่ปลอดภัย

```
[ External Real-Time Providers ]
  ├── Meteosource API (สภาพอากาศสด & พยากรณ์รายชั่วโมง)
  ├── JMA Japan Bosai (แผ่นดินไหว & การแจ้งเตือนภัยพิบัติฉุกเฉิน)
  ├── Yahoo Transit / ODPT (สถานะการเดินรถไฟสด JR Hokkaido 24 สาย)
  ├── AviationStack API (สถานะเที่ยวบิน CTS เข้า-ออก & การดีเลย์จากพายุหิมะ)
  ├── MLIT Road Information (การปิดทางด่วน & 7 ช่องเขาเสี่ยงภัยในฤดูหนาว)
  └── OSRM Routing Engine (ระยะทางและระยะเวลาเดินทาง)
                  │
                  ▼
[ 04_external_data_services ]
  ├── Sanitization & Validation (คัดกรองพารามิเตอร์ ป้องกัน Injection)
  ├── In-Memory CacheStore (TTL + Stale Fallback ป้องกัน Quota/Rate Limit)
  ├── Normalization Layer (แปลงผลลัพธ์เป็น LiveDataSnapshot สัญญามาตรฐาน)
  └── Agent Tool Schemas (JSON Schemas สำหรับ AI Function Calling)
                  │
                  ▼
[ Standardized LiveDataSnapshot Output ]
  (status: "ok" | "stale" | "unavailable", degraded: bool, data: dict, provenance intact)
```

---

### 1.1 สัญญาข้อมูลมาตรฐาน `LiveDataSnapshot` (`external_data/models.py`)
ทุก Adapter ในระบบส่งคืนผลลัพธ์ผ่านคลาส `LiveDataSnapshot` ซึ่งรับประกันความสม่ำเสมอของโครงสร้างข้อมูลทั่วทั้งแพลตฟอร์ม:
- **ฟิลด์สัญญาหลัก:**
  - `provider: str`: แหล่งที่มาของข้อมูล (เช่น `meteosource`, `jma`, `yahoo_transit`, `aviationstack`, `mlit_road`)
  - `kind: str`: ประเภทของข้อมูล (`weather`, `disaster`, `train`, `flight`, `road`, `route`)
  - `scope: str`: ขอบเขตที่สอบถาม (เช่น `Sapporo`, `Hokkaido`, `Rapid Airport`, `CTS`)
  - `status: str`: สถานะความสมบูรณ์ (`"ok"`, `"stale"`, `"unavailable"`, `"partial"`)
  - `degraded: bool`: บูลีนแจ้งเตือนความเสื่อมถอยของการเชื่อมต่อ (หาก `status != "ok"` จะเป็น `True` อัตโนมัติ)
  - `fetched_at: str`: เวลาที่ดึงข้อมูล (ISO 8601 UTC)
  - `expires_at: Optional[str]`: เวลาหมดอายุของแคช
  - `source_url: str`: ลิงก์อ้างอิงทางการเพื่อความโปร่งใส (Provenance)
  - `data: Dict[str, Any]`: ข้อมูลเนื้อหาที่ผ่านการ Normalize เรียบร้อย
  - `error_code: Optional[str]`: รหัสข้อผิดพลาดกรณีดึงไม่สำเร็จ (เช่น `TIMEOUT`, `CONFIG_MISSING`, `INVALID_INPUT`)
  - `notice: Optional[str]`: ข้อความอธิบายสถานะให้ Agent และระบบทราบ
- **ความเข้ากันได้แบบครอบคลุม:** รองรับการเข้าถึงแบบ `snapshot["data"]`, `snapshot.get(...)`, `to_dict()`, และ `to_json()`

---

### 1.2 รายละเอียดบริการและ Adapters ในระบบ

| บริการ (Service) | ไฟล์ Adapter | แหล่งข้อมูล (Source) | ฟังก์ชันหลัก / ขอบเขตข้อมูล | ระบบ Cache & Fallback |
|---|---|---|---|---|
| **สภาพอากาศสด (Weather)** | `external_data/weather.py` | Meteosource Weather API | ดึงอุณหภูมิ, สภาพอากาศ, ความเร็วลม, ปริมาณหิมะ, พยากรณ์รายชั่วโมงในเมืองท่องเที่ยวฮอกไกโด | TTL 10 นาที, Stale Cache Fallback |
| **ภัยพิบัติ & แผ่นดินไหว (Disaster)** | `external_data/disaster.py` | Japan Meteorological Agency (JMA Bosai Official Feeds) | ดึงข้อมูลแผ่นดินไหวล่าสุดในฮอกไกโด (พิกัด, ความลึก, ขนาดริกเตอร์, ความรุนแรงชินโดะ) และการแจ้งเตือนภัยพายุ/สึนามิ | TTL 2 นาที, แยกพิกัดเฉพาะฮอกไกโด |
| **รถไฟ JR Hokkaido สด (Trains)** | `external_data/train.py`, `external_data/trains.py` | Yahoo Transit Hokkaido & ODPT API | ตรวจสอบสถานะเดินรถไฟ 24 สาย (เช่น Hakodate Line, Chitose Line, Rapid Airport, Hokkaido Shinkansen) ตรวจจับความล่าช้า/งดเดินรถ | TTL 5 นาที, Stale Cache, **ไม่มโนข้อมูล** (คืน `unavailable` หากล่ม) |
| **เที่ยวบิน CTS (Flights)** | `external_data/flights.py` | AviationStack Flight API | ตรวจสอบเที่ยวบินเข้า-ออกสนามบิน New Chitose (CTS) และสนามบินภูมิภาค ตรวจจับเที่ยวบินดีเลย์ >15 นาที และเที่ยวบินยกเลิก | TTL 20 นาที, Stale Cache ป้องกันโควตา 100 req/เดือน |
| **สภาพถนน & ช่องเขา (Roads)** | `external_data/roads.py` | MLIT Hokkaido Road Information | ตรวจสอบการปิดทางด่วน (Do-O, Sasson, Doto) และ 4 ช่องเขาสำคัญ (Nakayama, Nissho, Sekihoku, Karikachi) จากหิมะ/น้ำแข็ง | TTL 10 นาที, วิเคราะห์คีย์เวิร์ดวิกฤต (`通行止`, `凍結`) |
| **คำนวณเส้นทาง (Routing)** | `external_data/routing.py` | OSRM Driving Engine | คำนวณระยะทาง (km) และระยะเวลาเดินทางโดยประมาณระหว่างจุดเริ่มต้นและปลายทาง | Direct HTTP Request |

---

### 1.3 ระบบคัดกรองและป้องกัน (Validation & Safety Layer)
- **`external_data/validation.py`:**
  - `validate_city(city_name)`: ตรวจสอบและแม็ปชื่อเมืองฮอกไกโด รองรับทั้งตัวพิมพ์เล็ก-ใหญ่ และอักขระพิเศษ
  - `validate_line_name(line_name)`: ตรวจสอบและแม็ปชื่อสายรถไฟทั้งภาษาอังกฤษและภาษาญี่ปุ่น
  - `validate_airport_code(airport_code)`: ตรวจสอบรหัสสนามบิน IATA/ICAO เฉพาะในฮอกไกโด (CTS, HKD, AKJ, WKJ, KUH, MMB, OBO)
  - `validate_region(region)`: ตรวจสอบขอบเขตภูมิภาค ป้องกันการป้อนพารามิเตอร์นอกพื้นที่หรือ Injection

---

### 1.4 Agent Function Calling Schemas (`external_data/tools.py`)
ลงทะเบียนเครื่องมือให้ Travel AI Agent (Node 03) สามารถตัดสินใจเรียกใช้งานแบบ Function Calling:
- `get_real_time_weather`: ตรวจสอบสภาพอากาศสด
- `get_disaster_warnings`: ตรวจสอบการแจ้งเตือนแผ่นดินไหวและสภาพอากาศฉุกเฉิน
- `check_train_status`: ตรวจสอบสถานะการเดินรถไฟสด
- `check_flight_status`: ตรวจสอบสถานะเที่ยวบิน CTS
- `check_road_status`: ตรวจสอบสภาพทางด่วนและช่องเขา
- `get_route_estimate`: ประมาณการระยะทางและเวลาเดินทาง

---

## 🛠️ 2. ปัญหาที่พบระหว่างทำและแนวทางแก้ไข (Problems Encountered & Technical Solutions)

ตลอดการพัฒนาระบบ ได้พบปัญหาทั้งด้านโครงสร้าง API ภายนอก, ปัญหาความเสถียร, นโยบายความถูกต้องของข้อมูล (No Hallucination), และการผสานรวมข้ามโหนด สรุปปัญหาและวิธีการแก้ไขดังตารางต่อไปนี้:

| ลำดับ | ปัญหาที่พบ (Problem) | สาเหตุที่แท้จริง (Root Cause) | แนวทางการแก้ไข (Technical Solution) |
|---|---|---|---|
| **1** | **ระบบ Mock สุ่มหน่วงเวลารถไฟ 20 นาที (`train.py`)** | มีการเขียนระบบ Simulator เดิมที่จำลองการดีเลย์ 20 นาที และอ้างสาเหตุ `track_snow_accumulation` เมื่อเกิดข้อผิดพลาดในการเชื่อมต่อ | **ยกเลิก Simulator และการมโนข้อมูลทั้งหมด 100%:** ปรับ `train.py` ให้เรียกข้อมูลสดจาก `fetch_live_train_status` หากเรียกไม่สำเร็จ ให้ส่งคืน `status="unavailable"` และ `error_code="TIMEOUT"`/`"FETCH_ERROR"` อย่างโปร่งใส โดย Agent จะได้รับคำแนะนำให้ผู้โดยสารสอบถามเจ้าหน้าที่ประจำสถานีโดยตรง |
| **2** | **Yahoo Transit RSS เดิมส่งกลับ 404 Not Found** | URL `/diainfo/rss/1/0` ที่ระบุในเอกสารตั้งต้นเป็นบริการเดิมที่ Yahoo Japan ยกเลิกการสนับสนุนไปแล้ว | พัฒนา Web Scraping Engine ดึงข้อมูลสดจากหน้าพอร์ทัลฮอกไกโดโดยตรง (`https://transit.yahoo.co.jp/diainfo/area/2`) ซึ่งส่งกลับ HTTP 200 และมีข้อมูลครบ 24 สาย |
| **3** | **AviationStack Free Tier ถูกปฏิเสธการเชื่อมต่อ HTTPS** | แผนบริการฟรีของ AviationStack ไม่อนุญาตให้เชื่อมต่อผ่าน HTTPS และจะส่ง Error Code `https_access_restricted` | ปรับ Base URL เป็น HTTP (`http://api.aviationstack.com/v1/flights`) สำหรับ Free Tier โดยเฉพาะ ทำให้เรียกใช้งานได้ราบรื่น |
| **4** | **โควตา Flight API มีจำกัดมาก (100 ครั้ง/เดือน)** | แผนบริการฟรีจำกัดโควตาไว้เพียง 100 ครั้งต่อเดือน ซึ่งอาจหมดลงอย่างรวดเร็วหากมีการค้นหาบ่อยครั้ง | 1. เพิ่ม Cache TTL เป็น 20 นาที (1200 วินาที)<br>2. พัฒนาระบบ **Stale Cache Fallback** หาก API แจ้งข้อผิดพลาด `usage_limit_reached` ระบบจะนำข้อมูลแคชล่าสุดมาส่งคืนพร้อมสถานะ `status="stale"` ทันที ทำให้ระบบไม่ล่ม |
| **5** | **พอร์ทัลข้อมูลถนน MLIT ไม่มี RSS Feed สำเร็จรูป** | ศูนย์ข้อมูลถนนฮอกไกโดไม่มีฟีด RSS รวมสำหรับการปิดเส้นทางในรูปแบบ JSON หรือ XML สำเร็จรูป | ออกแบบ Web Parser เจาะหน้าพอร์ทัลหลัก พร้อมวิเคราะห์คีย์เวิร์ดภาษาญี่ปุ่นที่บ่งบอกวิกฤต (`通行止` = ปิดการจราจร, `規制` = ควบคุม, `凍結` = ผิวทางน้ำแข็ง, `吹雪` = พายุหิมะ) มอนิเตอร์เฉพาะ 7 ทางด่วนและช่องเขายุทธศาสตร์ |
| **6** | **ความเสี่ยงระบบค้างจากเครือข่ายภายนอก (Network Latency & Hanging)** | การยิง HTTP Request ไปยังเว็บไซต์ทางการของญี่ปุ่นอาจเกิดความหน่วงสูงในช่วงเกิดพายุหิมะ | กำหนด `REQUEST_TIMEOUT_SECONDS = 3.0` วินาทีในทุก Adapter อย่างเข้มงวด พร้อมหุ้มด้วย `try-except` ส่งคืน `status="unavailable"` และ `degraded=True` ทันทีเมื่อหมดเวลา โดยไม่มีการ Crash |
| **7** | **โครงสร้างข้อมูล Train ไม่ตรงกับ Node 06 (`LocalRiskModel`)** | โมดูล 06 คาดหวังการอ่านคีย์ระดับบน เช่น `line_name`, `is_delayed`, `status` เพื่อนำไปคำนวณคะแนนความเสี่ยงทันที | ปรับ Normalized Data Dictionary ให้มีคีย์ระดับบนครบถ้วนทั้ง `line_name`, `status`, `is_delayed`, `disrupted_lines`, `all_lines` ทำให้ Node 06 ทำงานร่วมได้ 100% |
| **8** | **ความต้องการรองรับ Open Data for Public Transportation (ODPT)** | ต้องการเพิ่มตัวเลือกช่องทางข้อมูลรถไฟทางการของญี่ปุ่น นอกเหนือจากการสแครปหน้าเว็บ | เพิ่มฟังก์ชัน `_fetch_odpt_train_status` และรองรับ `ODPT_API_KEY` โดยระบบจะลองเรียก ODPT API ก่อน หากไม่มีคีย์หรือข้อมูลไม่สมบูรณ์จะสลับมาใช้ Yahoo Transit อัตโนมัติ |
| **9** | **รันการทดสอบบน Windows แล้วเจอ `UnicodeEncodeError` (CP1252)** | ข้อมูลหัวข้อแจ้งเตือนภัยพิบัติของ JMA มีอักขระภาษาญี่ปุ่นคันจิ/ฮิรางานะ (`石狩、空知...`) ซึ่ง Command Line บน Windows ค่าเริ่มต้นเป็น `cp1252` ทำให้เกิด Error ขณะ `print` | เพิ่มการกำหนดสภาพแวดล้อม `$env:PYTHONIOENCODING = "utf-8"` ในการรันสคริปต์ทดสอบ ทำให้รองรับอักขระภาษาญี่ปุ่นได้สมบูรณ์ |
| **10** | **ปัญหาการสลับ Git Branch และไฟล์ข้ามโหนดตกค้าง** | โฟลเดอร์งานเดิมอยู่ใน Branch เก่า (`feat/Optimize_...`) และมีไฟล์ที่ยังไม่ได้ Commit ของโหนดอื่น (`01`, `02`, `05`, `06`, `08`) ค้างอยู่ ทำให้ Git ปฏิเสธการสลับไปยัง Branch เป้าหมาย | 1. สำรองไฟล์ของโหนด 04 ไว้อย่างปลอดภัย<br>2. ใช้ `git stash push -u` เก็บการเปลี่ยนแปลงของโหนดอื่นทั้งหมด<br>3. สลับมายัง Branch `feat/add_04external_data_services`<br>4. นำไฟล์โหนด 04 กลับมา และตรวจสอบ `git status` ให้มีเฉพาะการเปลี่ยนแปลงใน `04_external_data_services/` เท่านั้น |
| **11** | **การปฏิบัติตามข้อกำหนด ห้ามมีลายน้ำ AI และจำกัดเฉพาะ Node 04** | ข้อกำหนดของผู้ใช้งานเข้มงวดเรื่องการห้ามมีลายน้ำ AI (`Copilot`, `ChatGPT`, `Claude`, `Gemini`), ห้ามมี `Co-authored-by` และห้ามแตะต้องโหนดอื่น | ตรวจสอบเนื้อหาของทุกไฟล์ด้วย Regex Search, ตรวจสอบ `git diff` เทียบกับ `develop`, และสร้าง Commit Message กับ Pull Request Description ในรูปแบบวิศวกรรมซอฟต์แวร์มาตรฐานที่สะอาดหมดจด |

---

## 🏛️ 3. กฎสถาปัตยกรรมและขอบเขตหน้าที่ (Strict Architectural Guardrails)

เพื่อให้ระบบเป็นไปตามหลักการ Separation of Concerns และมาตรฐานความปลอดภัยสูง:

1. **ห้ามตัดสินระดับความปลอดภัยเอง (No Direct Safety Verdicts):**
   - โหนด 04 มีหน้าที่คืนเฉพาะข้อมูลหลักฐานเชิงประจักษ์ (Normalized Evidence) เท่านั้น
   - **ไม่มีสิทธิ์** คำนวณค่า `safety_level` (เช่น `SAFE`, `DANGER`) หรือออกคำสั่งแนะนำการอพยพผู้ใช้เองโดยพลการ (หน้าที่นี้เป็นของ Node 06 และ Node 07)
2. **ห้ามปลอมแปลงความสำเร็จ (No Fabricated Success):**
   - หาก Provider ภายนอกไม่พร้อมให้บริการหรือ Timeout ระบบต้องรายงาน `status="unavailable"` หรือ `"stale"` อย่างตรงไปตรงมา ห้ามส่งข้อมูล Mock หลอกว่าบริการกำลังเปิดทำการปกติ
3. **การรักษาความโปร่งใสของที่มาข้อมูล (Data Provenance):**
   - ทุก Snapshot ต้องมี `source_url` และ `fetched_at` กำกับเสมอ เพื่อให้ผู้ใช้และโมดูลถัดไปสามารถตรวจสอบแหล่งที่มาได้

---

## 📊 4. สรุปผลการทดสอบและการนำขึ้นระบบ (Test & Delivery Results)

### 4.1 ชุดทดสอบ Unit & Integration Tests (100% Pass)
- รันชุดทดสอบ `04_external_data_services/tests/`: **79 เทส ผ่านทั้งหมด (79/79)**
  - `test_adapters.py`: 27 เทส (ครอบคลุม Weather, JMA, Live Trains, Flights, Roads, Tools)
  - `test_validation.py`: 18 เทส (ครอบคลุม City, Region, Line Name, Airport Code)
  - `test_models.py`: 10 เทส (ครอบคลุม LiveDataSnapshot, degraded flag, Dict conversion)
  - `test_cache.py`: 10 เทส (ครอบคลุม In-Memory Caching, TTL Expiry, Stale Fallback)
  - `test_integration.py`: 8 เทส (ครอบคลุม Tools Export, Contract Compliance)
  - `test_scenarios.py`: 6 เทส (ครอบคลุม End-to-End Real-World Scenarios)
- สคริปต์ `run_integration_tests.py`: **ผ่านครบทั้ง 3 สเตจ 100%**
  - Stage 1: Mock Contract Tests
  - Stage 2: Boot Integration Tests
  - Stage 3: End-to-End Scenario Testing (Safe, Degraded, Disaster Emergency)

### 4.2 การจัดส่งขึ้น GitHub (Git & PR Delivery)
- **Branch:** `feat/add_04external_data_services`
- **Commit:** `936e3c5` (`feat(04): replace mock train simulator with live transit feeds and ODPT support`)
- **Pull Request:** [PR #55](https://github.com/Automatic28m/safety_hokkaido/pull/55) เป้าหมายไปยังสาขา `develop`
- **ขอบเขต:** แก้ไขเฉพาะโฟลเดอร์ `04_external_data_services/` ไร้การแก้ไขในโหนดอื่น และไม่มีลายน้ำ AI ใดๆ
