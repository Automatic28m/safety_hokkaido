# 📋 รายงานวิเคราะห์การพัฒนา: เปรียบเทียบ main (ก่อนแยกโหนด) สู่ Node 04 (ปัจจุบัน)
**ระบบ Safety Hokkaido — การวิเคราะห์ความแตกต่าง, สิ่งที่พัฒนาเพิ่มเติม, ปัญหาที่พบ และแนวทางแก้ไข**

---

## 📌 1. จุดเริ่มต้นใน Branch `main` ดั้งเดิม (ก่อนการแยกโหนด)

ก่อนการปรับโครงสร้างระบบเป็น Modular Agentic Architecture ในสาขาหลัก (`main`) ข้อมูลภายนอกทั้งหมดถูกรวมอยู่ในไฟล์เดียวคือ `backend/src/tools.py` (ความยาวเพียง 104 บรรทัด) โดยมีข้อจำกัดและปัญหาสำคัญดังนี้:

### 1.1 ข้อมูลรถไฟเป็นการ "มโน" ข้อมูลขึ้นมาเอง 100% (Hardcoded Fabricated Data)
โค้ดใน `backend/src/tools.py` ของ `main` เดิม:
```python
def check_train_status(line_name: str = "All") -> str:
    """Checks the operational status of JR Hokkaido train lines."""
    # In a production environment, this would scrape JR Hokkaido's actual status page.
    # For this demo, we simulate a realistic winter status report.
    if "airport" in line_name.lower():
        return f"JR Hokkaido Status for {line_name}: Rapid Airport trains are experiencing 15-30 minute delays due to snow accumulation on the tracks. Please allow extra time for travel to New Chitose Airport."
    elif "hakodate" in line_name.lower():
        return f"JR Hokkaido Status for {line_name}: Running normally."
    else:
        return f"JR Hokkaido Status: Most lines are running normally. Localized delays of 10-15 minutes are occurring in the Sapporo area due to winter weather."
```
- **จุดบกพร่อง:** ไม่มีการเชื่อมต่ออินเทอร์เน็ต, ไม่มี API, และไม่มีการสแครปหน้าเว็บจริง เป็นเพียงการเขียนเงื่อนไข `if-else` สุ่มสร้างข้อความเท็จขึ้นมาหลอก Agent ว่ามีหิมะทับถมรางและดีเลย์ 15-30 นาที

### 1.2 ฮาร์ดโค้ดรหัสลับ API Key ลงในโค้ดโดยตรง (Hardcoded Secrets)
- ฟังก์ชันสภาพอากาศใส่รหัส API Key ของ Meteosource ลงในบรรทัดคำสั่งโดยตรง (`api_key = "nrv550ngnwo9vd4fdji129lpy7wlxk2xpn12czq0"`) ขัดต่อหลักความปลอดภัยและเสี่ยงต่อการรั่วไหล

### 1.3 รายงานภัยพิบัติไม่ได้ดึงการเตือนภัยสภาพอากาศจริง (Fake Weather Warnings)
- ฟังก์ชัน `get_disaster_warnings` เรียกเฉพาะ API แผ่นดินไหวของ JMA แต่ในส่วนของสภาพอากาศหนาวจัด/พายุหิมะ ฮาร์ดโค้ดข้อความหลอกไว้ว่า:
  `Snow Warnings: No severe blizzard warnings currently issued by JMA. Normal winter conditions apply.`
  โดยไม่ได้เชื่อมต่อฟีดการแจ้งเตือนภัยสภาพอากาศฉุกเฉินจริงของสำนักงานอุตุนิยมวิทยาญี่ปุ่น

### 1.4 รูปแบบข้อมูลส่งกลับเป็นข้อความดิบ (Unstructured Text)
- ทุกฟังก์ชันส่งคืนค่าเป็นสตริงก้อนเดียว (`str`) ทำให้ระบบปลายทาง (เช่น Node 06 Risk Knowledge และ Node 07 Decision Engine) ไม่สามารถนำค่าไปคำนวณความเสี่ยงเชิงตัวเลข, ไม่สามารถระบุความน่าเชื่อถือ, และไม่มีการบันทึกแหล่งที่มา (Provenance)

### 1.5 ขาดแคลนบริการสำคัญสำหรับความปลอดภัยในฮอกไกโด
- ❌ **ไม่มีข้อมูลเที่ยวบิน (Flight Status):** ไม่สามารถเช็กเที่ยวบินสนามบิน CTS ที่มักดีเลย์จากหิมะตกหนัก
- ❌ **ไม่มีข้อมูลสภาพถนนและช่องเขา (Road Conditions):** ไม่สามารถมอนิเตอร์การปิดทางด่วนและช่องเขาอันตราย
- ❌ **ไม่มีระบบคำนวณเส้นทาง (Routing):** ไม่สามารถคำนวณระยะทางและเวลาเดินทางจริง
- ❌ **ไม่มีระบบแคช (Cache Layer):** ยิง API ทุกครั้ง เสี่ยงต่อการโดนบล็อกหรือโควตาหมด
- ❌ **ไม่มีระบบคัดกรองข้อมูลนำเข้า (Sanitization/Validation):** เสี่ยงต่อ Injection
- ❌ **ไม่มีชุดทดสอบ (0 Unit Tests):** ขาดการรับประกันความเสถียรของระบบ

---

## 🚀 2. สิ่งที่อัปเดตและยกเครื่องใหม่ใน Node 04 ปัจจุบัน (`04_external_data_services`)

เราได้ปฏิรูปและแยกเป็นโหนดอิสระอย่างสมบูรณ์ โดยพัฒนาส่วนประกอบใหม่ทั้งหมด ดังนี้:

### 2.1 กำหนดสัญญาข้อมูลมาตรฐาน `LiveDataSnapshot` (`external_data/models.py`)
แปลงข้อมูลจากผู้ให้บริการทั้งหมดให้อยู่ในโครงสร้างมาตรฐานเดียวกัน:
- `provider`: แหล่งข้อมูลต้นทาง (`meteosource`, `jma`, `yahoo_transit`, `odpt_public_transport`, `aviationstack`, `hokkaido_road_info`, `osrm`)
- `kind`: ประเภทข้อมูล (`weather`, `disaster`, `train`, `flight`, `road`, `route`)
- `scope`: ขอบเขตพื้นที่หรือสายการเดินทาง (เช่น `Sapporo`, `Rapid Airport`, `CTS`, `Hokkaido`)
- `status`: สถานะผลลัพธ์ (`ok`, `stale`, `unavailable`, `partial`)
- `degraded`: บูลีนแจ้งเตือนความพร้อมของข้อมูล (หาก `status != "ok"` จะเป็น `True` ทันที)
- `fetched_at` & `expires_at`: วันเวลาที่บันทึกข้อมูลและวันหมดอายุของแคชตามมาตรฐาน ISO 8601 UTC
- `source_url`: URL ทางการของหน่วยงานเจ้าของข้อมูลเพื่อความโปร่งใสและตรวจสอบย้อนหลังได้ (Data Provenance)
- `data`: พจนานุกรมข้อมูลที่ผ่านการจัดโครงสร้าง (Normalize) พร้อมให้ Node 06 นำไปคำนวณต่อได้ทันที
- `error_code` & `notice`: แจ้งรหัสข้อผิดพลาดและข้อความแจ้งเตือนอย่างตรงไปตรงมา

### 2.2 ปลดระบบจำลอง/มโนข้อมูลออก แล้วเชื่อมต่อข้อมูลจริง 100%
- **รถไฟ JR Hokkaido (`external_data/train.py`, `external_data/trains.py`):**
  - ลบโค้ดสุ่มหน่วงเวลา 15-30 นาทีออกทั้งหมด
  - เชื่อมต่อระบบสแครปสถานะสดจากพอร์ทัลทางการ **Yahoo Transit Hokkaido ครบ 24 สาย**
  - รองรับ **ODPT (Open Data for Public Transportation) API** ผ่านคีย์ `ODPT_API_KEY`
  - หากเครือข่ายขัดข้อง จะส่งกลับ `status="unavailable"` และ `degraded=True` พร้อมแจ้งให้ผู้ใช้สอบถามเจ้าหน้าที่สถานีโดยตรง **ไม่มีการสร้างข้อมูลจำลองขึ้นมาเองอย่างเด็ดขาด**
- **ภัยพิบัติฉุกเฉินและแผ่นดินไหว (`external_data/disaster.py`):**
  - ดึงข้อมูลแผ่นดินไหวสดแบบเรียลไทม์ (พิกัด, ความลึก, แมกนิจูด, ชินโดะ) จาก JMA
  - เชื่อมต่อฟีดการแจ้งเตือนภัยสภาพอากาศฉุกเฉินจริง (พายุหิมะ, สึนามิ, ลมกระโชกแรง) ของ JMA Bosai เพื่อส่งข้อมูลเตือนภัยจริงสู่ระบบ

### 2.3 พัฒนาบริการใหม่ที่ไม่เคยมีมาก่อนใน `main`
- **ระบบสถานะเที่ยวบิน (`external_data/flights.py`):** เชื่อมต่อ AviationStack API เพื่อตรวจสอบเที่ยวบินเข้า-ออก สนามบิน New Chitose (CTS) และสนามบินภูมิภาค 7 แห่ง พร้อมตรวจจับเที่ยวบินดีเลย์และยกเลิกจากพายุหิมะ
- **ระบบสภาพถนนและช่องเขา (`external_data/roads.py`):** สแครปข้อมูลจากศูนย์ข้อมูลถนนฮอกไกโด (MLIT) มอนิเตอร์การปิดทางด่วน 3 สาย และ 4 ช่องเขายุทธศาสตร์ฤดูหนาว (Nakayama, Nissho, Sekihoku, Karikachi Pass)
- **ระบบประมาณการเส้นทาง (`external_data/routing.py`):** เชื่อมต่อ OSRM Driving Engine เพื่อคำนวณระยะทางและระยะเวลาเดินทางจริง

### 2.4 ระบบแคชและการรักษาความปลอดภัย
- **In-Memory CacheStore (`external_data/cache.py`):** แคชข้อมูลตามช่วงเวลา TTL ที่เหมาะสมในแต่ละบริการ พร้อมระบบ **Stale Cache Fallback** นำข้อมูลล่าสุดมาใช้งานชั่วคราวเมื่อ API ภายนอกขัดข้องหรือโควตาเต็ม
- **Input Validation (`external_data/validation.py`):** คัดกรองและปรับมาตรฐานชื่อเมือง, สายรถไฟ, ภูมิภาค, และรหัสสนามบิน ป้องกัน Injection และลดภาระของเครือข่าย

### 2.5 ชุดทดสอบครบวงจร (Automated Test Coverage)
- พัฒนาชุดทดสอบในโฟลเดอร์ `tests/` รวม **81 Unit Tests (ผ่าน 100%)**
- สคริปต์ `run_integration_tests.py` ตรวจสอบความถูกต้องครบทั้ง 3 สเตจ (Schema Contract, Module Boot, End-to-End Scenarios)

---

## 🛠️ 3. ปัญหาที่พบระหว่างทำและแนวทางแก้ไข (Problems & Solutions)

| ลำดับ | ปัญหาที่พบ (Problem) | สาเหตุที่แท้จริง (Root Cause) | วิธีการแก้ไข (Resolution) |
|---|---|---|---|
| **1** | **ระบบเดิมมี Mock สุ่มหน่วงเวลารถไฟ 20 นาที (`train.py`)** | โค้ดเดิมจำลองการดีเลย์ 20 นาที และระบุสาเหตุ `track_snow_accumulation` เมื่อเกิดข้อผิดพลาดในการเชื่อมต่อ | **ยกเลิกระบบ Simulator และการมโนข้อมูลออกทั้งหมด 100%:** ปรับ `train.py` ให้เรียก `fetch_live_train_status` หากเรียกไม่สำเร็จให้ส่งคืน `status="unavailable"` และ `error_code="TIMEOUT"`/`"FETCH_ERROR"` อย่างโปร่งใส โดย Agent จะได้รับคำแนะนำให้ผู้โดยสารสอบถามเจ้าหน้าที่ประจำสถานีโดยตรง |
| **2** | **Yahoo Transit RSS เดิมส่งกลับ 404 Not Found** | URL `/diainfo/rss/1/0` เป็น URL เก่าที่ทาง Yahoo Japan ยกเลิกบริการไปแล้ว | พัฒนา Web Scraping Parser ดึงข้อมูลสดจากหน้าพอร์ทัลฮอกไกโดโดยตรง (`https://transit.yahoo.co.jp/diainfo/area/2`) ซึ่งส่งกลับข้อมูลสถานะ 24 สายแบบเรียลไทม์ |
| **3** | **AviationStack Free Tier ถูกบล็อก HTTPS** | แผนบริการฟรีของ AviationStack ไม่อนุญาตให้เชื่อมต่อผ่าน HTTPS (`https_access_restricted`) | ปรับ Base URL เป็น HTTP (`http://api.aviationstack.com/v1/flights`) สำหรับ Free Tier โดยเฉพาะ ทำให้เรียกใช้งานได้ตามปกติ |
| **4** | **โควตา Flight API มีจำกัด (100 ครั้ง/เดือน)** | Free tier จำกัดเพียง 100 ครั้งต่อเดือน ซึ่งอาจหมดลงอย่างรวดเร็ว | 1. ขยาย Cache TTL เป็น 20 นาที (1200 วินาที)<br>2. พัฒนาระบบ **Stale Cache Fallback** หาก API แจ้งข้อผิดพลาด `usage_limit_reached` ระบบจะนำข้อมูลแคชล่าสุดมาส่งคืนพร้อมสถานะ `status="stale"` ทันที ทำให้ระบบไม่ล่ม |
| **5** | **พอร์ทัลข้อมูลถนน MLIT ไม่มี RSS Feed สำเร็จรูป** | ศูนย์ข้อมูลถนนฮอกไกโดไม่มีฟีด RSS รวมสำหรับการปิดเส้นทางในรูปแบบ JSON/XML สำเร็จรูป | ออกแบบ Web Parser วิเคราะห์คีย์เวิร์ดภาษาญี่ปุ่นที่บ่งบอกวิกฤต (`通行止` = ปิดการจราจร, `規制` = ควบคุม, `凍結` = ผิวทางน้ำแข็ง, `吹雪` = พายุหิมะ) มอนิเตอร์เฉพาะ 7 ทางด่วนและช่องเขายุทธศาสตร์ |
| **6** | **ความเสี่ยงระบบค้างจากเครือข่ายภายนอก (Latency & Hanging)** | การยิง HTTP Request ไปยังเว็บไซต์ทางการของญี่ปุ่นอาจเกิดความหน่วงสูงในช่วงเกิดพายุหิมะ | กำหนด `REQUEST_TIMEOUT_SECONDS = 3.0` วินาทีในทุก Adapter พร้อมหุ้มด้วย `try-except` ส่งคืน `status="unavailable"` และ `degraded=True` ทันทีเมื่อหมดเวลา โดยไม่มีการ Crash |
| **7** | **โครงสร้างข้อมูล Train ไม่ตรงกับ Node 06 (`LocalRiskModel`)** | โมดูล 06 คาดหวังการอ่านคีย์ระดับบน เช่น `line_name`, `is_delayed`, `status` เพื่อนำไปคำนวณคะแนนความเสี่ยงทันที | ปรับ Normalized Data Dictionary ให้มีคีย์ระดับบนครบถ้วนทั้ง `line_name`, `status`, `is_delayed`, `disrupted_lines`, `all_lines` ทำให้ Node 06 ประเมินความเสี่ยงได้โดยตรง |
| **8** | **การรองรับ Open Data for Public Transportation (ODPT)** | ต้องการเพิ่มตัวเลือกช่องทางข้อมูลรถไฟทางการของญี่ปุ่น นอกเหนือจากการสแครปหน้าเว็บ | เพิ่มฟังก์ชัน `_fetch_odpt_train_status` และรองรับ `ODPT_API_KEY` พร้อมแยก `_normalize_odpt_response` กรองสายรถไฟตามที่ผู้ใช้ร้องขอ และสลับมาใช้ Yahoo Transit อัตโนมัติหากไม่มีคีย์ |
| **9** | **การทดสอบบน Windows พบ `UnicodeEncodeError` (CP1252)** | ข้อความแจ้งเตือนภัยพิบัติของ JMA มีอักขระภาษาญี่ปุ่นคันจิ/ฮิรางานะ (`石狩、空知...`) ซึ่ง Command Line บน Windows มีค่าเริ่มต้นเป็น `cp1252` ทำให้เกิด Error ขณะ `print` | เพิ่มการกำหนดสภาพแวดล้อม `$env:PYTHONIOENCODING = "utf-8"` ในการรันสคริปต์ทดสอบ ทำให้รองรับอักขระภาษาญี่ปุ่นได้สมบูรณ์ |
| **10** | **ปัญหาการสลับ Git Branch และไฟล์ข้ามโหนดตกค้าง** | โฟลเดอร์งานเดิมอยู่ใน Branch เก่า (`feat/Optimize_...`) และมีไฟล์ที่ยังไม่ได้ Commit ของโหนดอื่นค้างอยู่ ทำให้ Git ปฏิเสธการสลับไปยัง Branch เป้าหมาย | 1. สำรองไฟล์ของโหนด 04 ไว้อย่างปลอดภัย<br>2. ใช้ `git stash push -u` เก็บการเปลี่ยนแปลงของโหนดอื่นทั้งหมด<br>3. สลับมายัง Branch `feat/add_04external_data_services`<br>4. นำไฟล์โหนด 04 กลับมา และตรวจสอบ `git status` ให้มีเฉพาะการเปลี่ยนแปลงใน `04_external_data_services/` เท่านั้น |
| **11** | **การปฏิบัติตามข้อกำหนด ห้ามมีลายน้ำ AI และจำกัดเฉพาะ Node 04** | ข้อกำหนดของผู้ใช้งานเข้มงวดเรื่องการห้ามมีลายน้ำ AI (`Copilot`, `ChatGPT`, `Claude`, `Gemini`), ห้ามมี `Co-authored-by` และห้ามแตะต้องโหนดอื่น | ตรวจสอบเนื้อหาของทุกไฟล์ด้วย Regex Search, ตรวจสอบ `git diff` เทียบกับ `develop`, และสร้าง Commit Message กับ Pull Request Description ในรูปแบบวิศวกรรมซอฟต์แวร์มาตรฐานที่สะอาดหมดจด |

---

## 📊 4. ตารางเปรียบเทียบ Before (`main`) vs After (Node 04 ปัจจุบัน)

| คุณสมบัติ (Feature) | ใน Branch `main` เดิม (ก่อนแยกโหนด) | ใน Node 04 ปัจจุบัน (`feat/add_04...`) |
|---|---|---|
| **โครงสร้างสถาปัตยกรรม** | รวมอยู่ใน `backend/src/tools.py` รวมศูนย์กับระบบอื่น | แยกเป็นแพ็กเกจอิสระ `04_external_data_services/` มีขอบเขตชัดเจน |
| **รูปแบบข้อมูลส่งกลับ** | สตริงก้อนเดียว (`str`) แยกแยะโครงสร้างไม่ได้ | โครงสร้าง `LiveDataSnapshot` มีสถานะ `status`, `degraded`, `source_url`, `data` |
| **การจัดการความลับ (Secrets)** | ฮาร์ดโค้ด API Key ในซอร์สโค้ดโดยตรง | จัดการผ่านสภาพแวดล้อม `.env` (`METEOSOURCE_API_KEY`, `ODPT_API_KEY`) |
| **ความถูกต้องของข้อมูลรถไฟ** | สุ่มข้อความดีเลย์ 15-30 นาที (`if-else` มโน) | ดึงสดจาก Yahoo Transit 24 สาย + ODPT API (ไม่มโน คืน `unavailable` เมื่อมีปัญหา) |
| **การแจ้งเตือนภัยพิบัติ** | ดึงเฉพาะแผ่นดินไหว (ส่วนพายุหิมะฮาร์ดโค้ดข้อความหลอกไว้) | ดึงสดทั้งแผ่นดินไหวและการแจ้งเตือนสภาพอากาศฉุกเฉินจริงจาก JMA |
| **สถานะเที่ยวบิน CTS** | ❌ ไม่มี | ✅ มี (`flights.py` รองรับ New Chitose และ 7 สนามบินภูมิภาค) |
| **สภาพถนนและช่องเขา** | ❌ ไม่มี | ✅ มี (`roads.py` สแครป MLIT มอนิเตอร์ 7 ทางด่วนและช่องเขา) |
| **คำนวณเส้นทาง** | ❌ ไม่มี | ✅ มี (`routing.py` เชื่อมต่อ OSRM Driving Engine) |
| **ระบบแคชและป้องกันโควตา** | ❌ ไม่มี (ยิงสดทุกครั้ง เสี่ยงติด Rate Limit) | ✅ มี In-Memory CacheStore พร้อมระบบ Stale Cache Fallback |
| **การคัดกรองข้อมูลนำเข้า** | ❌ ไม่มี | ✅ มี `validation.py` คัดกรองเมือง, สายรถไฟ, รหัสสนามบิน ป้องกัน Injection |
| **การรับประกันคุณภาพ** | ❌ ไม่มีชุดทดสอบ (0 Unit Tests) | ✅ 81 Unit Tests (ผ่าน 100%) + สคริปต์รัน Integration 3 สเตจ |
