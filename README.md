# ความสามารถหลักของโปรเจกต์ Safety Hokkaido (Project Capabilities)

**Safety Hokkaido** ไม่ใช่แค่เพียงแชตบอทนำเที่ยวทั่วไป แต่เป็น **"ระบบ AI ผู้ช่วยและเฝ้าระวังความปลอดภัยอัจฉริยะสำหรับนักท่องเที่ยว"** (Intelligent Tourist Safety & Guide Agent) โดยเฉพาะในภูมิภาคฮอกไกโด ประเทศญี่ปุ่น ซึ่งมีความเสี่ยงด้านสภาพอากาศสุดขั้วและภัยพิบัติ

นี่คือความสามารถและจุดเด่นหลัก (Key Capabilities) ของระบบนี้:

## 1. ผู้ช่วยนำเที่ยวที่ตอบโต้ได้หลายภาษา (Multilingual Persona)
*   **Tamago (ทามาโกะ):** AI ประจำแอปพลิเคชันที่ถูกออกแบบให้มีบุคลิกอบอุ่น เป็นมิตร และสุภาพ 
*   **Cross-Lingual Support:** ผู้ใช้สามารถพิมพ์ถามเป็นภาษาไทย ภาษาอังกฤษ หรือภาษาอื่น ๆ ระบบจะทำการวิเคราะห์ ค้นหาข้อมูล และตอบกลับเป็นภาษาเดียวกับที่ผู้ใช้ถามมาโดยอัตโนมัติ 
*   **Dynamic Tone Adaptation:** แม้ปกติจะตอบอย่างเป็นมิตร แต่หากตรวจพบว่าเกิดภัยพิบัติหรือผู้ใช้อยู่ในอันตราย AI จะปรับโทนเสียงให้ **จริงจัง กระชับ และเน้นความปลอดภัยเป็นอันดับแรก** ทันที

## 2. การดึงข้อมูลแบบเรียลไทม์ (Real-Time Live Snapshots)
ระบบสามารถเชื่อมต่อกับบริการภายนอกเพื่อให้ได้ข้อมูลที่สดใหม่ที่สุด ณ ขณะนั้น (Node 04):
*   **Weather API:** ตรวจสอบสภาพอากาศปัจจุบัน อุณหภูมิ และพายุหิมะ 
*   **Disaster Warnings (JMA):** รับประกาศเตือนภัยแผ่นดินไหว สึนามิ และภัยพิบัติอื่น ๆ จากกรมอุตุนิยมวิทยาญี่ปุ่น
*   **Transit & Train Status (JR Hokkaido):** ตรวจสอบสถานะการเดินรถไฟ การดีเลย์ หรือการหยุดวิ่งชั่วคราวแบบเรียลไทม์

## 3. ระบบค้นหาความรู้เชิงลึกแบบ Hybrid (Hybrid RAG System)
*   ระบบไม่ได้ใช้แค่ความรู้เดิมของ AI (ซึ่งเสี่ยงต่อการ "มั่ว" ข้อมูล) แต่ใช้ระบบ **RAG (Retrieval-Augmented Generation)** (Node 05, 06)
*   สามารถค้นหาคู่มือรับมือภัยพิบัติ เอกสารแนะนำจาก JNTO หรือคู่มือการขับรถในฮอกไกโด (PDFs/JSON) แบบเจาะลึก 
*   ใช้การค้นหาแบบลูกผสม ทั้ง **FAISS (Dense/Semantic Search)** เพื่อหาความหมาย และ **BM25 (Keyword Search)** เพื่อหาคำเฉพาะเจาะจง จากนั้นนำมาประเมินคะแนน (Rerank) เพื่อให้ได้ข้อมูลที่แม่นยำที่สุด

## 4. ระบบการตัดสินใจที่มีความปลอดภัยขั้นสูงสุด (Strict Guardrails & Synthesizer)
*   **No Hallucination (ห้ามมั่วข้อมูล):** AI ไม่มีสิทธิ์จินตนาการเส้นทางหนีภัย หรือแต่งตัวเลขขึ้นมาเองเด็ดขาด (Node 07)
*   **Evidence-Based Only:** AI จะต้องใช้เฉพาะ "หลักฐานอ้างอิง" และ "ข้อมูลเรียลไทม์" ที่ระบบเตรียมให้เท่านั้น หากข้อมูลไม่เพียงพอ AI ถูกบังคับให้ตอบว่า *"ไม่มีข้อมูลเพียงพอ"* แทนการสุ่มเดา
*   **Source Citation (การอ้างอิง):** ทุกคำตอบจะมีการแนบ `Evidence ID` หรือ `Live Source` กลับมา เพื่อให้ตรวจสอบย้อนหลัง (Audit) ได้เสมอว่า AI เอาข้อมูลมาจากไหน
*   **Fail-Safe:** ถ้าระบบหลังบ้านล่ม หรือต่อ API ของกรมอุตุนิยมวิทยาไม่ได้ AI จะระบุอย่างชัดเจนว่าระบบขัดข้อง (Degraded Mode) เพื่อไม่ให้นักท่องเที่ยวเข้าใจผิดว่าสถานการณ์ปลอดภัย

## 5. สถาปัตยกรรมแบบ Micro-Module (Highly Decoupled Architecture)
*   แยกการทำงานออกเป็น 8 โมดูลอย่างเด็ดขาด (เช่น ตัวหาข้อมูล กับ ตัวตัดสินใจ แยกกันคนละห้อง) 
*   ทำให้ระบบมีความเสถียรสูง ป้องกันไม่ให้ AI แอบเรียกใช้ API โดยพลการ และทำให้ทีมนักพัฒนาหลายๆ ทีมสามารถทำงานพร้อมกันได้โดยไม่ทำให้โค้ดพัง (Safe to scale)

---
**สรุป:** Safety Hokkaido คือระบบที่ผสานระหว่าง **ความสะดวกสบายในการท่องเที่ยว** กับ **มาตรฐานความปลอดภัยสูงสุดยามฉุกเฉิน** ผ่านเทคโนโลยี AI ที่ถูกตีกรอบการทำงานอย่างรัดกุมที่สุด

# โครงสร้างโฟลเดอร์ของโปรเจกต์ Safety Hokkaido (Project Structure)

โปรเจกต์ **Safety Hokkaido** ถูกแบ่งออกเป็น 8 โมดูลหลักอย่างเป็นระบบ (Microservice-oriented architecture) เพื่อให้แต่ละทีมสามารถพัฒนา ทดสอบ และแก้ไขโค้ดในส่วนของตัวเองได้โดยไม่กระทบกัน 

ด้านล่างนี้คือโครงสร้างโฟลเดอร์หลักของโปรเจกต์ พร้อมคำอธิบายหน้าที่ของแต่ละส่วน

```text
safety_hokkaido/
├── 01_web_app/                     # โมดูลที่ 1: ส่วนเชื่อมต่อผู้ใช้งาน (Frontend)
│   ├── src/                        # Source code หลักของ Next.js (UI, ChatBot, Map)
│   ├── public/                     # ไฟล์ Static (รูปภาพ, ไอคอน)
│   ├── messages/                   # ไฟล์ Locale (รองรับหลายภาษา เช่น ไทย, อังกฤษ)
│   ├── package.json                # ไฟล์จัดการ Dependencies ของ Node.js
│   └── (ไฟล์ Fix/Update ต่างๆ ที่ใช้ในฝั่ง UI)
│
├── 02_api_backend/                 # โมดูลที่ 2: ระบบศูนย์กลาง API (FastAPI)
│   ├── main.py                     # Entry point หลักของเซิร์ฟเวอร์ (Routing, CORS)
│   ├── config.py                   # ไฟล์ตั้งค่ารวม (Environment variables)
│   ├── api/                        # ตัวจัดการ HTTP Request / Response 
│   ├── src/                        # Logic หลังบ้านที่ใช้ร่วมกัน
│   ├── data/                       # ข้อมูลคู่มือและเอกสารต้นฉบับ
│   ├── vector_db/                  # ฐานข้อมูล Vector (สำหรับค้นหาข้อมูล)
│   └── tests/                      # Unit Tests ของระบบ API
│
├── 03_travel_ai_agent/             # โมดูลที่ 3: ระบบควบคุมและจัดการ Workflow (Orchestrator)
│   ├── agent_core/                 # Logic ตัดสินใจเส้นทาง (Route), เก็บ Memory และคุม State
│   └── 01_env.md - 03_process.md   # เอกสารออกแบบการทำงานของ Agent
│
├── 04_external_data_services/      # โมดูลที่ 4: ตัวเชื่อมต่อข้อมูลภายนอกแบบเรียลไทม์
│   ├── external_data/              # Adapters เชื่อม JMA (ภัยพิบัติ), JR (รถไฟ), Weather API
│   └── tests/                      # Unit Tests สำหรับตรวจสอบการดึงข้อมูล
│
├── 05_data_integration/            # โมดูลที่ 5: ระบบเตรียมข้อมูลและสร้างฐานความรู้
│   ├── data_integration/           # ระบบ Ingestion, ทำ Chunking และสร้าง Embeddings
│   └── tests/                      # Unit Tests สำหรับตรวจสอบ Data Pipeline
│
├── 06_risk_knowledge_services/     # โมดูลที่ 6: ระบบค้นหาข้อมูลความเสี่ยง (Retrieve & Rerank)
│   ├── risk_knowledge/             # ดึง Evidence จาก FAISS/BM25 พร้อมประเมิน Rank
│   └── tests/                      # Unit Tests สำหรับระบบค้นหา
│
├── 07_decision_llm_engine/         # โมดูลที่ 7: ระบบสังเคราะห์คำตอบ (Controlled Synthesizer)
│   ├── decision_engine/            # คุยกับ LLM, แปลผล JSON, จำกัดขอบเขตไม่ให้มั่ว (No Hallucination)
│   └── 01_env.md - 03_process.md   # เอกสารกฎเหล็กการทำงาน (Guardrails)
│
├── 08_recommendation_feedback/     # โมดูลที่ 8: ระบบเก็บข้อมูลและประเมินผล (Audit & Eval)
│   ├── recommendation_feedback/    # เก็บ Feedback (Thumbs up/down)
│   ├── app.py / service.py         # บริการแยกสำหรับจัดการข้อมูล Log
│   └── evaluate.py                 # สคริปต์ประเมินความแม่นยำของ AI
│
├── .github/                        # (ซ่อน) ระบบ CI/CD และ Automation
│   ├── scripts/                    # สคริปต์ AI Reviewer
│   ├── rules/                      # กฎ Architecture Guidelines ของทีม
│   └── workflows/                  # GitHub Actions (เช่น แจ้งเตือน Discord)
│
├── README.md                       # เอกสารแนะนำโปรเจกต์
└── runtime.py                      # สคริปต์รัน Environment กลาง
```

# การแบ่งงานและมอบหมายหน้าที่ (Module Assignment)

ตารางด้านล่างนี้แสดงการแบ่งงานของโปรเจกต์ Safety Hokkaido ตามโครงสร้าง 8 โมดูลหลัก โดยระบุรายละเอียดงาน ผู้รับผิดชอบ และบัญชี GitHub ของผู้รับผิดชอบ

| Module | ชื่อโมดูล | รายละเอียดงาน (Task Description) | ผู้รับผิดชอบ (Assignee) | GitHub |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **Web App** | จัดการ UI, Locale (ภาษา), หน้าต่างแชต และแสดงผลสถานะต่าง ๆ จาก Backend (ห้ามตัดสินใจ Safety เอง และห้ามเก็บ API Key ฝั่ง Browser) | นายอรัญ โต๊ะสู | `https://github.com/rdyAran` |
| **02** | **API Backend** | จัดการ HTTP Validation, CORS, Request/Response Schema และตรวจสอบ Error (เช่น คืนค่า 400/503/500 ให้ถูกต้อง ไม่ใช้ 200 ตอนพัง) | นายชลากร ศรีบุญเรือง | `https://github.com/fffalafair` |
| **03** | **Travel AI Agent** | เป็น Orchestrator หลัก จัดการ Context/Session ของผู้ใช้ (ผ่าน `conversation_id`) และเป็นตัวเรียก API ของ Node 04, 06 | Nuthaluek kokotsomrong | `https://github.com/Onpreyaq5` |
| **04** | **External Data Services** | สร้าง Adapter สำหรับเชื่อมต่อ Weather API, ข่าวสารภัยพิบัติ (JMA) และตารางรถไฟ (JR) โดยแปลงเป็น `LiveDataSnapshot` | ศรัญ ธัญญวิกัย | `https://github.com/hoh251` |
| **05** | **Data Integration** | รับผิดชอบเรื่อง Data Pipeline, Ingestion, ตัดคำ (Chunking), การทำ Embeddings และการสร้าง Index (FAISS + BM25) | วิศรุต ขำหล่อ | `https://github.com/wissarut-29` |
| **06** | **Risk Knowledge Services** | ดูแลระบบ Retrieve & Rerank ดึงข้อมูลจากฐานความรู้ (PDF/คู่มือ) คืนค่า Evidence พร้อมคะแนน Rank และ Provenance | ชีวากร อาจดีลัง | `https://github.com/cheewakornartdeelang` |
| **07** | **Decision LLM Engine** | นำ Evidence และ Live Data มาสังเคราะห์คำตอบสุดท้าย (Controlled Synthesizer) โดยห้ามเรียก API อินเทอร์เน็ตเองเด็ดขาด | พัลลภ บุญเหลือ | `https://github.com/Automatic28m` |
| **08** | **Recommendation Feedback** | ดูแลระบบ Logging, Evaluation, และรับ Feedback (Thumbs up/down) จากผู้ใช้ เพื่อนำไปทำ Audit Trace | มาริสา พิมพระลับ | `https://github.com/marisa46054` |

---