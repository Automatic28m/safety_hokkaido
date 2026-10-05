# 📌 สรุปรายงานการพัฒนา: 05_data_integration (Safety Hokkaido)
**เอกสารสรุปผลการดำเนินงาน, ปัญหาที่พบ, วิธีแก้ไข, และชุดเครื่องมือที่ใช้**

---

## 🎯 1. สิ่งที่เราทำไปทั้งหมด (What Was Done)

เราได้ทำการพัฒนาและปรับปรุงโมดูล `05_data_integration` ใหม่ทั้งหมด เพื่อให้สอดคล้องกับข้อกำหนดใน `05_data_integration_implementation_plan.md` และวิสัยทัศน์ของระบบใน `project_master_brief_th.md` โดยมีรายละเอียดดังนี้:

### 1.1 สกัดข้อมูล PDF แยกรายหน้าและเก็บ Page Provenance (ที่มาเลขหน้า)
* ปรับปรุงกระบวนการอ่าน PDF ให้วนอ่านทีละหน้า (`page.extract_text()`) และหั่น Chunk ภายในหน้านั้นๆ
* ระบุ `page` (เลขหน้า 1-based) ลงใน Metadata ของทุก Chunk เพื่อให้ระบบสามารถอ้างอิงย้อนหลังได้ 100% (Traceability)

### 1.2 สร้าง Stable Chunk ID แบบ Deterministic
* เลิกใช้ตัวนับลำดับตัวเลข (`chunk_id_counter`) หรือลำดับ `glob` ที่อาจเปลี่ยนแปลงตาม OS
* เปลี่ยนมาใช้สูตรสร้าง ID ที่คงที่และตรวจสอบย้อนหลังได้:
  * **PDF:** `{clean_stem}_p{page:03d}_c{chunk_index:03d}` (เช่น `avoid_frostbite_p001_c000`)
  * **JSON:** `{clean_stem}_{sit_hash}_c{chunk_index:03d}`
  * **TXT:** `{clean_stem}_c{chunk_index:03d}`

### 1.3 ขยายและปรับโครงสร้าง Metadata ให้สมบูรณ์ (พร้อมคง Backward Compatibility)
* เพิ่มฟิลด์ตรวจสอบความถูกต้อง:
  * `source_version`: แฮช SHA-256 ของไฟล์ต้นฉบับ (16 ตัวแรก)
  * `reviewed_at`: เวลาที่มีการตรวจสอบหรืออัปเดตไฟล์ (ISO 8601 UTC)
  * `page`: เลขหน้าของเอกสาร
* รักษาฟิลด์เดิมไว้ครบถ้วน (`text`, `metadata.source_file`, `metadata.category`, `metadata.situation`, `metadata.url`) เพื่อไม่ให้โมดูลอื่น (06, 07) เกิดข้อผิดพลาด

### 1.4 ป้องกันชุดข้อสอบรั่วไหล (Strict Golden Set Exclusion)
* ตรวจสอบและข้ามไฟล์ `golden_set.json` เสมอ เพื่อไม่ให้นำข้อสอบสำหรับประเมินผล (โมดูล 08) เข้ามาปนในคลังความรู้ของ AI

### 1.5 สร้างระบบ Data Models & Contract ชัดเจน
* สร้าง `models.py` โดยใช้ Pydantic:
  * `ChunkMetadata`: กำหนดสเปก Metadata ของแต่ละ Chunk
  * `DocumentChunk`: กำหนดโครงสร้าง Chunk พร้อมฟังก์ชัน `.to_dict()`
  * `ChunkSettings`: เก็บค่าตั้งค่าขนาด Chunk และ Overlap
  * `IndexManifest`: สเปก Manifest ของ Index ทั้งหมด

### 1.6 ระบบ Index Manifest & Fingerprint Caching
* พัฒนา `IndexManifest` บันทึก: `schema_version`, `index_version`, `corpus_hash`, `embedding_model`, `chunk_settings`, `build_time`, `total_chunks`, `total_sources`, `source_files`
* ตรวจสอบ Staleness ด้วย SHA-256 ของคลังข้อมูล หากข้อมูลไม่เปลี่ยนแปลง ระบบจะ Skip การ build อัตโนมัติ

### 1.7 ระบบ Atomic Publishing & Rollback Protection
* แก้ไข `VectorStore` ให้สร้างไฟล์ทั้งหมด (`document.index`, `bm25_index.pkl`, `chunk_store.json`, `index_meta.json`) ในโฟลเดอร์ชั่วคราว (`.staging_...`) ก่อน
* มีขั้นตอนตรวจสอบความถูกต้อง (Verify) หากไฟล์ครบและอ่านได้จริง จึงสลับโฟลเดอร์ (Atomic Swap) เข้าสู่ตำแหน่งจริง หากเกิดข้อผิดพลาดจะ Rollback คืนค่าเดิมทันที

### 1.8 แยกการพึ่งพาโมดูล (Decoupling) และทำ Pipeline Orchestrator
* กำหนดค่า Default Parameters ภายใน `text_splitter.py` ไม่ผูกติดกับ config ของโมดูล 02
* สร้าง `builder.py` มีฟังก์ชัน `run_index_build()` เป็นจุดรวมการทำงานของ Pipeline ทั้งหมด

### 1.9 สร้างชุดทดสอบอัตโนมัติ (Automated Tests)
* สร้าง Unit Tests และ Integration Tests ใน `05_data_integration/tests/` ครอบคลุม 17 Test cases (ผ่าน 100%)

---

## ⚠️ 2. ปัญหาที่พบระหว่างทาง (Problems Encountered)

1. **ปัญหาเลขหน้าหายไปใน PDF เดิม:**
   * *สาเหตุ:* โค้ดเก่าเอาข้อความทุกหน้าของ PDF มารวมเป็นสตริงก้อนเดียวด้วย `raw_text += text + "\n"` ก่อนนำไปหั่น Chunk ทำให้สูญเสียข้อมูลว่าเนื้อหานั้นมาจากหน้าใด
2. **ปัญหา Chunk ID ไม่คงที่ (Non-deterministic IDs):**
   * *สาเหตุ:* ใช้ `chunk_id_counter` ที่เพิ่มทีละ 1 ตามลำดับการอ่านไฟล์จากไดเรกทอรี หากรันต่างเครื่องหรือระบบไฟล์เรียงลำดับต่างกัน จะได้ Chunk ID ไม่ตรงกัน ทำให้โมดูล 08 ตรวจสอบย้อนหลังไม่ได้
3. **ความเสี่ยง Index เสียหายจากการเขียนทับโดยตรง (Non-atomic writes):**
   * *สาเหตุ:* โค้ดเดิมเขียนไฟล์ลงโฟลเดอร์เป้าหมายทันที หากโปรเซสล่มกลางคันระหว่างทำ Embeddings หรือ Index จะทิ้งไฟล์ที่พังหรือไม่สมบูรณ์ไว้ใน Production
4. **ความไม่ยืดหยุ่นและการปนเปื้อนของข้อมูล JSON:**
   * *สาเหตุ:* หากมีฟิลด์ `situation` หรือ `advices` เป็น `null` หรือไม่ใช่ List โค้ดจะหยุดทำงานหรือข้ามไปโดยไม่จัดการ
5. **ข้อผิดพลาด Unicode บน Windows Console (`charmap` Codec Error):**
   * *สาเหตุ:* Windows Terminal บางเครื่องใช้ Codepage ภาษาไทย/อังกฤษ (เช่น `cp1252`) เมื่อโค้ดมี Emoji อย่าง `⚠️` หรือ `✅` จะเกิด `UnicodeEncodeError`
6. **การพึ่งพิงข้ามโมดูล (Tight Coupling):**
   * *สาเหตุ:* `text_splitter.py` เรียกใช้ `from config import config` ข้ามไปยังโมดูล `02_api_backend` ทำให้โมดูล 05 ไม่สามารถรันแยกเป็นอิสระได้
7. **Environment เริ่มต้นยังขาด Library สำคัญ:**
   * *สาเหตุ:* ยังไม่ได้ติดตั้ง `pypdf`, `langchain-text-splitters`, และ `python-dotenv` ในเครื่อง

---

## 🛠️ 3. วิธีการแก้ไขและเครื่องมือที่ใช้ (Solutions & Tools Used)

| ปัญหาที่พบ | วิธีการแก้ไข | เครื่องมือ / เทคโนโลยีที่ใช้ |
|---|---|---|
| **Page Provenance หาย** | วนลูปอ่านทีละหน้า `reader.pages` แล้วหั่น Chunk แยกตามหน้า พร้อมใส่ `page=page_idx` ใน Metadata | `pypdf.PdfReader` |
| **Chunk ID ไม่คงที่** | ออกแบบโครงสร้าง ID แบบ Deterministic โดยใช้ File Stem + Page Number + Chunk Index และแฮชของ Situation | `hashlib` (MD5/SHA256), `re` (Regex Sanitization) |
| **ความเสี่ยง Index เสียหาย** | ทำ Staging Directory (`.staging_...`) เมื่อสร้างเสร็จและ Verify ทุกไฟล์ผ่าน จึงทำ Atomic Rename/Swap เข้าแทนที่ | `os.rename`, `shutil.rmtree`, `uuid` |
| **ข้อมูล JSON มี Null / ผิดฟอร์แมต** | เพิ่ม Sanitization และ Type Checking: ตรวจสอบ Null, แปลงเป็นค่าเริ่มต้นที่ปลอดภัย, กรอง Advice ที่ว่างเปล่าออก | Python Type Guards & Default fallbacks |
| **UnicodeEncodeError บน Windows** | เพิ่มคำสั่ง `sys.stdout.reconfigure(encoding='utf-8')` ใน Entrypoint เพื่อรองรับ UTF-8 บน Windows Console | Python `sys.stdout` |
| **Module Coupling** | กำหนด Default Settings (`CHUNK_SIZE=400`, `CHUNK_OVERLAP=50`) ในตัวโมดูล 05 และอนุญาตให้ส่งผ่าน Constructor ได้ | Python Default Arguments & Fallback Import |
| **Dependencies ขาด** | ติดตั้งแพ็กเกจที่ระบุในข้อกำหนดผ่าน Python Module Installer | `python -m pip install pypdf langchain-text-splitters python-dotenv` |
| **ขาดการทดสอบ** | เขียนชุดทดสอบครบทั้ง Loader, Splitter, Meta, Manifest, Vector Store และ Rollback Mechanism | `pytest` (17 Test Cases ผ่านทั้งหมด) |

---

## 📊 4. สรุปชุดเครื่องมือและไลบรารีทั้งหมด (Technology Stack)

* **ภาษาหลัก:** Python 3.13
* **Data Ingestion & PDF:** `pypdf` (สกัดข้อความแยกหน้า)
* **Text Chunking:** `langchain-text-splitters` (`RecursiveCharacterTextSplitter`)
* **Vector Index (Dense):** `faiss-cpu` (`IndexFlatL2`)
* **Keyword Index (Sparse):** `rank_bm25` (`BM25Okapi`)
* **Embedding Model:** `sentence-transformers` (โมเดล `all-MiniLM-L6-v2`)
* **Data Modeling & Validation:** `pydantic` (BaseModel, Field)
* **Cryptographic & Integrity:** `hashlib` (SHA-256 Fingerprinting)
* **Testing Framework:** `pytest`

---

## 🧪 5. ผลการทดสอบยืนยันระบบ (Test & Verification Results)

1. **Unit & Integration Tests:**
   * รันคำสั่ง `pytest 05_data_integration/tests`
   * ผลลัพธ์: **17 passed** จาก 17 รายการ (100% Pass)
2. **การทดสอบสร้าง Index บนข้อมูลจริงของโปรเจกต์:**
   * สกัดข้อมูลจากเอกสารจริง **30 ไฟล์** (PDF 25 ไฟล์ + JSON 5 ไฟล์)
   * ได้ Chunk ทั้งหมด **575 Chunks** โดยทุก Chunk จาก PDF มี `page` กำกับครบ 100%
   * ทดสอบรันซ้ำ: ระบบข้ามการ build โดยแจ้ง `Data has not changed since the last build. Skipping database generation to save time!` ได้ถูกต้อง
3. **การทดสอบ Integration กับโมดูล 06 (`HybridRetriever`):**
   * ทดสอบส่ง Query ฉุกเฉิน: *"What is the emergency number for ambulance in Hokkaido?"*
   * ผลลัพธ์: ดึงข้อมูลจาก Index ชุดใหม่ได้ 3 Chunks ที่ตรงเป้าหมายทันที (มี Chunk ID, Source, Situation, และ Page ครบถ้วน)

---

## 📝 6. Template / Prompt สำหรับส่งรายงาน Pull Request ให้ทีมงาน

สามารถนำข้อความด้านล่างนี้ไปใช้เป็น **PR Description** หรือส่งรายงานในทีมได้ทันที:

```markdown
### 🚀 PR Title: feat(data_integration): implement page provenance, stable IDs, manifest, and atomic vector store

#### 📋 Summary of Changes
- **Page Provenance:** Slices PDF documents on a per-page basis, preserving `page` number in chunk metadata for 100% traceability.
- **Stable Chunk IDs:** Replaced global counters with deterministic IDs based on file stem, page, and chunk index.
- **Traceability Metadata:** Added `source_version` (SHA-256 fingerprint) and `reviewed_at` (ISO timestamp) while strictly preserving all legacy consumer fields.
- **Golden Set Exclusion:** Enforced strict filtering to exclude `golden_set.json` from the emergency index.
- **Index Manifest & Freshness:** Added `IndexManifest` tracking corpus hash, model, chunk settings, and build timestamp.
- **Atomic Publishing & Rollback:** Uses staging directories and atomic directory swaps to prevent partial/corrupted index states.
- **Decoupled Architecture:** Removed cross-module dependencies and created standalone models and builder pipeline.
- **Testing:** Added 17 unit and integration tests (100% passing). Tested against the full 30-document corpus (575 chunks).
```
