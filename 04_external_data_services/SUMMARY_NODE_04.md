# 📋 สรุปภาพรวมการพัฒนา โมดูล 04: External Data Services
**ระบบ Safety Hokkaido — รายละเอียดการเพิ่มฟังก์ชัน, การแก้ปัญหาทางเทคนิค, และขอบเขตหน้าที่ของโหนด**

---

## 🎯 1. เราเพิ่มอะไรไปบ้าง (What Was Added)

เพื่อให้สอดคล้องกับข้อกำหนดในแผนพัฒนาโมดูล 04 (`แผนการพัฒนา Module 04: External Data`) และสัญญาของระบบ (`SAFETY_HOKKAIDO_NODE_CONTRACT.md`) โดยคงขอบเขตการทำงานให้อยู่เฉพาะภายในโฟลเดอร์ `04_external_data_services/` อย่างเคร่งครัด เราได้พัฒนาและเพิ่มเติมระบบหลักดังนี้:

### 1.1 Live JR Hokkaido Train Status Adapter (`external_data/trains.py`)
- **การดึงข้อมูลสด:** สแครปสถานะสดการเดินรถไฟ 24 สายของ JR Hokkaido ผ่านหน้าพอร์ทัลทางการของ Yahoo Transit Hokkaido (`https://transit.yahoo.co.jp/diainfo/area/2`)
- **การแม็ปและสกัดข้อมูล:** รองรับชื่อสายรถไฟทั้งภาษาอังกฤษและภาษาญี่ปุ่น เช่น Hakodate Line, Chitose Line, Sassho Line, Sekihoku Line, Rapid Airport, Hokkaido Shinkansen
- **ความเข้ากันได้กับ Node 06:** ส่งมอบโครงสร้างข้อมูลระดับบน (`line_name`, `status`, `is_delayed`, `disrupted_lines`, `all_lines`) ช่วยให้ `LocalRiskModel` (โมดูล 06) คำนวณคะแนนความเสี่ยงได้ทันที
- **Safety Fallback:** ตั้งเวลา Timeout 3.0 วินาที พร้อมส่งสถานะ `degraded=True` และ `status="unavailable"` หรือ `"stale"` หากต่อเครือข่ายไม่ติด โดยไม่มีการ Crash

### 1.2 AviationStack Flight Status Adapter (`external_data/flights.py`)
- **ตรวจสอบสถานะเที่ยวบิน:** รองรับสนามบินหลัก 7 แห่งในฮอกไกโด (CTS - New Chitose, HKD - Hakodate, AKJ - Asahikawa, WKJ - Wakkanai, KUH - Kushiro, MMB - Memanbetsu, OBO - Obihiro)
- **การตรวจจับความผิดปกติ:** สกัดข้อมูลเที่ยวบินดีเลย์ (Delay > 15 นาที) และเที่ยวบินที่ถูกยกเลิก (Cancelled) อันเนื่องมาจากสภาพอากาศหนาวจัดหรือพายุหิมะ
- **ระบบป้องกันโควตา (Quota Protection):** ตั้งค่า Cache TTL ไว้ที่ 20 นาที (`DEFAULT_FLIGHT_TTL = 1200`) และมีระบบ Stale Cache Fallback อัตโนมัติเมื่อโควตารายเดือนเต็ม

### 1.3 MLIT Hokkaido Road Conditions Adapter (`external_data/roads.py`)
- **ตรวจสอบสภาพถนนและช่องเขา:** ดึงข้อมูลจากพอร์ทัลศูนย์พัฒนาภูมิภาคฮอกไกโด กระทรวงที่ดิน โครงสร้างพื้นฐาน การขนส่ง และการท่องเที่ยวญี่ปุ่น (MLIT Hokkaido Road Info: `https://www.road-info-prvs.mlit.go.jp/`)
- **การวิเคราะห์คีย์เวิร์ดวิกฤต:** ตรวจจับคำว่า การปิดถนน (`通行止`), การควบคุมการจราจร (`規制`), ผิวทางเป็นน้ำแข็ง (`凍結`), และพายุหิมะทัศนวิสัยเป็นศูนย์ (`吹雪`)
- **มอนิเตอร์ 7 เส้นทางยุทธศาสตร์ฤดูหนาว:**
  1. ทางด่วน Do-O Expressway
  2. ทางด่วน Sasson Expressway
  3. ทางด่วน Doto Expressway
  4. ช่องเขานากายามะ (Nakayama Pass - Route 230)
  5. ช่องเขานิชโชะ (Nissho Pass - Route 274)
  6. ช่องเขาเซกิโฮคุ (Sekihoku Pass - Route 39)
  7. ช่องเขาคาริคาจิ (Karikachi Pass - Route 38)
- ตั้งค่า Cache TTL 10 นาที (600 วินาที) และ Timeout 3.0 วินาที

### 1.4 ปรับปรุงสัญญาข้อมูล `LiveDataSnapshot` (`external_data/models.py`)
- เพิ่มแอตทริบิวต์ `degraded: Optional[bool] = None`
- มีระบบประเมินผลอัตโนมัติใน `__post_init__`: หาก `status != "ok"` (เช่น `unavailable`, `stale`, `mocked`) จะตั้งค่า `degraded = True` ทันที ตอบโจทย์แผนพัฒนาโดยไม่กระทบโค้ดเดิม
- รองรับการเข้าถึงข้อมูลแบบ Dictionary Subscript (`snapshot['key']`), `.get()`, `.to_dict()`, และ `.to_json()` ได้อย่างสมบูรณ์

### 1.5 ตัวคัดกรองข้อมูลนำเข้า (`external_data/validation.py`)
- เพิ่มฟังก์ชัน `validate_airport_code(airport_code)` ตรวจสอบรหัส IATA/ICAO ให้อยู่ในขอบเขตฮอกไกโด ป้องกัน Injection และป้องกัน Invalid Input
- คงการตรวจสอบ `validate_city`, `validate_region`, `validate_line_name` อย่างรัดกุม

### 1.6 การลงทะเบียน Tool Wrappers สำหรับ Agent (`external_data/tools.py` & `__init__.py`)
- ประกาศ Tool Schemas และฟังก์ชันสำหรับ AI Function Calling ให้ Node 03 (Travel AI Agent) เรียกใช้งาน:
  - `LIVE_TRAIN_TOOL_SCHEMA` & `check_live_train_status(line_name)`
  - `FLIGHT_TOOL_SCHEMA` & `check_flight_status(airport_code, flight_type)`
  - `ROAD_TOOL_SCHEMA` & `check_road_status(region_or_pass)`
  - `WEATHER_TOOL_SCHEMA` & `get_real_time_weather(city)`
  - `DISASTER_TOOL_SCHEMA` & `get_disaster_warnings(region)`
  - `ROUTE_TOOL_SCHEMA` & `get_route_estimate(origin, destination, mode)`
- Export ทุกฟังก์ชันและคลาสผ่าน `external_data/__init__.py` อย่างสะอาด

### 1.7 ชุดทดสอบครบวงจร (Full Test Suite)
- ขยาย Unit & Functional Tests ในโฟลเดอร์ `tests/` รวม **79 เทส ผ่านรวด 100%**:
  - `test_adapters.py`: 27 เทส (ทดสอบ Weather, JMA, Train, Flight, Road, Tools)
  - `test_validation.py`: 18 เทส (ทดสอบ Validation ครบทุกมิติรวม Airport)
  - `test_models.py`: 10 เทส (ทดสอบ LiveDataSnapshot และ degraded flag)
  - `test_cache.py`: 10 เทส (ทดสอบ In-memory Cache, Expiry, Stale Fallback)
  - `test_integration.py`: 8 เทส (ทดสอบ Contract & Re-exports)
  - `test_scenarios.py`: 6 เทส (ทดสอบสถานการณ์จริง 3 รูปแบบ)
- สคริปต์ `run_integration_tests.py`: รัน 3 สเตจ (Mock Contract, Boot, End-to-End Scenarios) ผ่านสมบูรณ์

---

## 🛠️ 2. แก้ปัญหาอะไรบ้าง จากสาเหตุอะไร (Problems & Technical Solutions)

| ปัญหาที่พบ | สาเหตุ (Root Cause) | วิธีการแก้ไข (Resolution) |
|---|---|---|
| **1. Yahoo Transit RSS ส่งกลับ 404 Not Found** | URL `/diainfo/rss/1/0` ในแผนเดิมเป็น URL เก่าที่ทาง Yahoo Japan ยกเลิกบริการไปแล้ว | ปรับสถาปัตยกรรมมาใช้ Web Scraping จากหน้าแสดงสถานะทางการของภูมิภาคฮอกไกโดโดยตรง (`https://transit.yahoo.co.jp/diainfo/area/2`) ซึ่งส่งกลับ HTTP 200 พร้อมข้อมูลสถานะ 24 สายแบบเรียลไทม์ |
| **2. AviationStack Free Tier ติด Error `https_access_restricted`** | Free Tier ของ AviationStack บังคับส่งผ่าน HTTP เท่านั้น หากเรียกผ่าน HTTPS จะถูกบล็อก | กำหนด Base URL ให้เป็น `http://api.aviationstack.com/v1/flights` โดยตรง ทำให้ยิง API ได้ตามปกติ |
| **3. ความเสี่ยงโควตา API เที่ยวบินหมด (100 req/month)** | แผนบริการฟรีจำกัดโควตาไว้เพียง 100 ครั้งต่อเดือน ซึ่งอาจหมดลงอย่างรวดเร็ว | 1. ขยาย Cache TTL เป็น 20 นาที (`1200 วินาที`) สูงกว่าเกณฑ์ขั้นต่ำในแผน<br>2. เพิ่มระบบ Stale Cache Fallback หากพบโค้ดข้อผิดพลาด `usage_limit_reached` ระบบจะส่งข้อมูลแคชล่าสุดพร้อมสถานะ `stale` ทันที ทำให้ระบบไม่ล่ม |
| **4. พอร์ทัลปิดถนน MLIT ไม่มี RSS Feed สำเร็จรูป** | ศูนย์ข้อมูลถนนฮอกไกโด MLIT ไม่มีฟีด RSS เฉพาะสำหรับการปิดเส้นทาง | ออกแบบ Web Parser เจาะหน้าพอร์ทัลหลัก พร้อมวิเคราะห์คีย์เวิร์ดภาษาญี่ปุ่น (`通行止`, `規制`, `凍結`, `吹雪`) กรองเฉพาะ 7 เส้นทางและช่องเขาสำคัญ |
| **5. ความหน่วงของเครือข่ายภายนอก (Latency & Hanging Risk)** | เครือข่ายภายนอก (เช่น Yahoo, MLIT, AviationStack) อาจช้าหรือ Timeout ในช่วงพายุเข้า | บังคับใช้ Strict Timeout ไม่เกิน 3.0 วินาที ทุก Adapter และหุ้มด้วย `try-except` คืนสถานะ `unavailable` พร้อม `degraded=True` ทันทีหากต่อไม่ติด |
| **6. โครงสร้างข้อมูล Train ไม่ตรงกับ Node 06** | โมดูล 06 (`LocalRiskModel`) อ่านค่าคีย์ระดับบน เช่น `line_name`, `is_delayed`, `status` หากซ้อนลึกจะอ่านไม่เจอ | จัดรูป Data Dictionary ของ Train Snapshot ให้มีคีย์ทั้งระดับบนและรายละเอียดครบถ้วน ทำให้ Node 06 ประเมินความเสี่ยงได้โดยตรง |
| **7. ข้อผิดพลาดการทดสอบข้ามโหนด (Cross-module Coupling)** | `test_integration.py` เดิมอ้างอิง `src.tools` ของ Node 02 ทำให้เมื่อรันเทสเฉพาะโหนด 04 โดดๆ จะหาโมดูลไม่เจอ | ปรับปรุงชุดทดสอบให้ตรวจสอบการ Export ของแพ็กเกจ `external_data` ของโหนด 04 เองโดยตรง ทำให้เทสเป็นอิสระ (Decoupled) 100% |

---

## 🏛️ 3. ในโหนดของเรามีหน้าที่ทำอะไรได้ (Responsibilities & Capabilities)

### 3.1 หน้าที่หลักของโหนด 04 (Core Responsibilities)
1. **เป็น Single Source of Truth สำหรับข้อมูลภายนอก (External Data Provider):**
   - ทำหน้าที่เชื่อมต่อเครือข่ายภายนอก ดึงข้อมูลสด และกลั่นกรองข้อมูล Real-Time จากแหล่งข้อมูลที่เชื่อถือได้
2. **ปรับข้อมูลให้อยู่ในสัญญามาตรฐาน (Data Normalization):**
   - แปลงข้อมูลที่ได้จากหลายผู้ให้บริการ (JMA, Meteosource, Yahoo, AviationStack, MLIT, OSRM) ให้อยู่ในโมเดลเดียวกันคือ `LiveDataSnapshot`
3. **ระบบแคชและปกป้องโควตา (Caching Layer):**
   - บริหารจัดการหน่วยความจำแคชเพื่อลด Latency และป้องกัน Rate Limit / Quota Exhaustion
4. **ความปลอดภัยและการตรวจสอบข้อมูลนำเข้า (Sanitization & Validation):**
   - ตรวจสอบชื่อเมือง, สายรถไฟ, ภูมิภาค, และรหัสสนามบิน ป้องกันการยิง Prompt Injection หรือคำสั่งที่ไม่ปลอดภัยมายัง Provider ภายนอก
5. **สร้าง Tool Interface ให้ Agent ใช้งาน:**
   - มอบ Function Calling Schemas ให้ Node 03 (Travel AI Agent) ตัดสินใจเลือกเรียกใช้ได้อย่างมีประสิทธิภาพ

### 3.2 ความสามารถของโหนด 04 ในปัจจุบัน (What It Can Do)
- 🌤️ **สภาพอากาศสด (Weather):** ตรวจสอบอุณหภูมิ, สภาพอากาศ, ลม, หิมะ และความชื้นในฮอกไกโด (เช่น Sapporo, Otaru, Asahikawa, Hakodate, Furano, Niseko)
- ⚠️ **ภัยพิบัติสด (Disaster & Warnings):** ดึงข้อมูลแผ่นดินไหวแบบเรียลไทม์ และการแจ้งเตือนภัย/สภาพอากาศรุนแรงจากสำนักงานอุตุนิยมวิทยาญี่ปุ่น (JMA)
- 🚆 **สถานะรถไฟสด (Live Train Status):** ตรวจสอบการล่าช้าหรือการงดเดินรถไฟ JR Hokkaido 24 สาย
- ✈️ **สถานะเที่ยวบิน (Flight Status):** ตรวจสอบเที่ยวบินเข้า-ออก สนามบิน New Chitose (CTS) และสนามบินภูมิภาค ตรวจจับเที่ยวบินดีเลย์และยกเลิก
- 🚗 **สภาพถนนและช่องเขา (Road Conditions):** ตรวจสอบการปิดทางด่วนและช่องเขา 7 แห่งจากพายุหิมะและผิวทางเป็นน้ำแข็ง
- 🗺️ **ประมาณระยะทางและเวลาเดินทาง (Route Estimation):** คำนวณระยะทางและระยะเวลาเดินทางระหว่างเมืองผ่าน OSRM

### 3.3 ขอบเขตและข้อห้ามตามกฎสถาปัตยกรรม (Strict Architecture Guardrails)
- ❌ **ห้ามตัดสินระดับความปลอดภัยเอง:** โหนด 04 มีหน้าที่คืนเฉพาะข้อมูลหลักฐาน (Normalized Evidence) เท่านั้น **ไม่มีสิทธิ์** คำนวณคะแนนความปลอดภัย (`safety_level`) หรือสั่งอพยพผู้ใช้เองเด็ดขาด (เป็นหน้าที่ของ Node 07: Decision LLM Engine)
- ❌ **ห้ามปลอมแปลงความสำเร็จ (No Fabricated Success):** หาก Provider ภายนอกล่ม ต้องส่งสถานะ `unavailable` หรือ `stale` พร้อมระบุสาเหตุ ห้ามส่งข้อมูล Mock หลอกว่าระบบภายนอกปกติ
- ❌ **ห้ามมี AI Watermark:** โค้ดและเอกสารทั้งหมดต้องปลอดจากลายน้ำหรือ Contributor AI อย่างเด็ดขาด
