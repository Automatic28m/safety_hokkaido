# ความสามารถหลักของโปรเจกต์ Safety Hokkaido (Project Capabilities)

**Safety Hokkaido** ไม่ใช่แค่เพียงแชตบอทนำเที่ยวทั่วไป แต่เป็น **"ระบบ AI ผู้ช่วยและเฝ้าระวังความปลอดภัยอัจฉริยะสำหรับนักท่องเที่ยว"** (Intelligent Tourist Safety & Guide Agent) โดยเฉพาะในภูมิภาคฮอกไกโด ประเทศญี่ปุ่น ซึ่งมีความเสี่ยงด้านสภาพอากาศสุดขั้วและภัยพิบัติ

นี่คือความสามารถและจุดเด่นหลัก (Key Capabilities) **ที่อัปเดตล่าสุด** ของระบบนี้:

## 1. ผู้ช่วยนำเที่ยวที่ตอบโต้ได้หลายภาษา (Multilingual Persona)
*   **Tamago (ทามาโกะ):** AI ประจำแอปพลิเคชันที่ถูกออกแบบให้มีบุคลิกอบอุ่น เป็นมิตร และสุภาพ 
*   **Cross-Lingual Support:** ผู้ใช้สามารถพิมพ์ถามเป็นภาษาไทย ภาษาอังกฤษ หรือภาษาอื่น ๆ ระบบจะทำการวิเคราะห์ ค้นหาข้อมูล และตอบกลับเป็นภาษาเดียวกับที่ผู้ใช้ถามมาโดยอัตโนมัติ 
*   **Dynamic Tone Adaptation:** แม้ปกติจะตอบอย่างเป็นมิตร แต่หากตรวจพบว่าเกิดภัยพิบัติหรือผู้ใช้อยู่ในอันตราย AI จะปรับโทนเสียงให้ **จริงจัง กระชับ และเน้นความปลอดภัยเป็นอันดับแรก** ทันที

## 2. การดึงข้อมูลแบบเรียลไทม์ (Real-Time Live Snapshots)
ระบบสามารถเชื่อมต่อกับบริการ API ภายนอกเพื่อให้ได้ข้อมูลที่สดใหม่ที่สุด (Node 04):
*   **Weather API:** ตรวจสอบสภาพอากาศปัจจุบัน อุณหภูมิ และพายุหิมะ 
*   **AviationStack (Flights):** ตรวจสอบข้อมูลและสถานะเที่ยวบินแบบเรียลไทม์ (มีการบริหารจัดการ API Quota อย่างรัดกุม)
*   **Disaster Warnings (JMA):** รับประกาศเตือนภัยแผ่นดินไหว สึนามิ และภัยพิบัติอื่น ๆ จากกรมอุตุนิยมวิทยาญี่ปุ่น
*   **Transit & Train Status (JR Hokkaido):** ตรวจสอบสถานะการเดินรถไฟ การดีเลย์ แบบเรียลไทม์

## 3. ระบบค้นหาความรู้เชิงลึกแบบ Hybrid (Hybrid RAG System)
*   ขับเคลื่อนด้วยระบบค้นหาแบบลูกผสม ทั้ง **FAISS (Dense/Semantic Search)** และ **BM25 (Keyword Search)** (Node 05, 06)
*   ใช้ Embedding Model ประสิทธิภาพสูง (`sentence-transformers/all-MiniLM-L6-v2`) ในการค้นหาจากฐานความรู้ เช่น คู่มือรับมือภัยพิบัติ เอกสาร JNTO เพื่อป้องกันการมั่วข้อมูลของ AI

## 4. ระบบการตัดสินใจและขุมพลัง LLM (Decision LLM Engine & Guardrails)
*   **Groq API (Llama 3 / Mixtral):** ประมวลผล ตัดสินใจ และสังเคราะห์คำตอบด้วยความเร็วสูงมากผ่านชิป LPU ของ Groq (Node 07)
*   **Evidence-Based Only:** AI จะต้องใช้เฉพาะ "หลักฐานอ้างอิง" และ "ข้อมูลเรียลไทม์" เท่านั้น หากไม่มีข้อมูล AI ถูกบังคับให้ตอบว่า *"ไม่มีข้อมูลเพียงพอ"* แทนการสุ่มเดา
*   **Source Citation:** ทุกคำตอบจะมีการแนบ `Evidence ID` หรือ `Live Source` กลับมา เพื่อให้ตรวจสอบย้อนหลังได้เสมอ

---

# โครงสร้างโฟลเดอร์ของโปรเจกต์ Safety Hokkaido (Project Structure)

โปรเจกต์ **Safety Hokkaido** ถูกแบ่งออกเป็น 8 โมดูลหลักอย่างเป็นระบบ (Microservice-oriented architecture) เพื่อให้แต่ละทีมสามารถพัฒนา ทดสอบ และแก้ไขโค้ดในส่วนของตัวเองได้โดยไม่กระทบกัน 

ด้านล่างนี้คือโครงสร้างโฟลเดอร์หลักของโปรเจกต์ พร้อมคำอธิบายหน้าที่ของแต่ละส่วน

```text
safety_hokkaido/
├── 01_web_app/                     # โมดูลที่ 1: ส่วนเชื่อมต่อผู้ใช้งาน (Frontend)
├── 02_api_backend/                 # โมดูลที่ 2: ระบบศูนย์กลาง API (FastAPI)
├── 03_travel_ai_agent/             # โมดูลที่ 3: ระบบควบคุมและจัดการ Workflow (Orchestrator)
├── 04_external_data_services/      # โมดูลที่ 4: ตัวเชื่อมต่อข้อมูลภายนอกแบบเรียลไทม์ (Weather, Flights, JR)
├── 05_data_integration/            # โมดูลที่ 5: ระบบเตรียมข้อมูล ทำ Chunking และสร้างฐานข้อมูล Vector
├── 06_risk_knowledge_services/     # โมดูลที่ 6: ระบบค้นหาข้อมูลความเสี่ยง (Retrieve & Rerank)
├── 07_decision_llm_engine/         # โมดูลที่ 7: ระบบสังเคราะห์คำตอบ (Controlled Synthesizer ด้วย Groq)
├── 08_recommendation_feedback/     # โมดูลที่ 8: ระบบเก็บข้อมูลและประเมินผล (ปิดการใช้งานชั่วคราว)
├── .github/                        # (ซ่อน) ระบบ CI/CD และ Automation
├── docker-compose.yml              # ไฟล์สำหรับ Deployment รันระบบผ่าน Docker บน Hostinger VPS
├── DEPLOYMENT.md                   # คู่มือการนำระบบขึ้น Hostinger VPS
└── README.md                       # เอกสารแนะนำโปรเจกต์
```

# การแบ่งงานและมอบหมายหน้าที่ (Module Assignment & Workload)

ตารางด้านล่างนี้แสดงการแบ่งงานของโปรเจกต์ Safety Hokkaido ตามโครงสร้าง 8 โมดูลหลัก โดยระบุผู้รับผิดชอบหลัก และ **สัดส่วนภาระงานจริง (Workload Percentage)** ของสมาชิกแต่ละคนในโมดูลนั้นๆ

| Module | ชื่อโมดูล | รายละเอียดงาน (Task Description) | ผู้รับผิดชอบหลัก (Main Assignee) | สัดส่วนภาระงานจริง (Workload %) |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **Web App** | จัดการ UI, Locale, หน้าต่างแชต (ลบ Mapbox API และปรับ Transportation เป็น Static Layout) | นายอรัญ โต๊ะสู | พัลลภ บุญเหลือ (70%)<br>นายอรัญ โต๊ะสู (30%) |
| **02** | **API Backend** | จัดการ FastAPI, HTTP Validation, CORS, และ Proxy | นายชลากร ศรีบุญเรือง | นายชลากร ศรีบุญเรือง (100%) |
| **03** | **Travel AI Agent** | Orchestrator หลัก จัดการ Context/Session ผ่าน `conversation_id` | Nuthaluek kokotsomrong | Nuthaluek kokotsomrong (100%) |
| **04** | **External Data Services** | สร้าง Adapter เชื่อม Weather API, JMA, JR และข้อมูลเที่ยวบินจาก AviationStack | ศรัญ ธัญญวิกัย | ศรัญ ธัญญวิกัย (100%) |
| **05** | **Data Integration** | Data Pipeline, Page Provenance, Stable IDs, ตัดคำ (Chunking), FAISS + BM25 | วิศรุต ขำหล่อ | ชีวากร อาจดีลัง (100%) |
| **06** | **Risk Knowledge Services** | ดูแลระบบ Retrieve & Rerank, Unified Facade, การพยากรณ์ความเสี่ยงล่วงหน้า, ตัวคูณจุดเสี่ยง | ชีวากร อาจดีลัง | ชีวากร อาจดีลัง (100%) |
| **07** | **Decision LLM Engine** | สังเคราะห์คำตอบสุดท้ายด้วย Groq API (Controlled Synthesizer) โดยยึด Evidence เป็นหลัก | พัลลภ บุญเหลือ | พัลลภ บุญเหลือ (100%) |
| **08** | **Recommendation Feedback** | ระบบ Logging และ Audit | มาริสา พิมพระลับ | มาริสา พิมพระลับ (100%) |

---


# ผู้จัดทำและ GitHub Links (Team Members)

- **พัลลภ บุญเหลือ** - [Automatic28m](https://github.com/Automatic28m)
- **มาริสา พิมพระลับ** - [marisa46054](https://github.com/marisa46054)
- **นายอรัญ โต๊ะสู** - [rdyAran](https://github.com/rdyAran)
- **นายชลากร ศรีบุญเรือง** - [fffalafair](https://github.com/fffalafair)
- **Nuthaluek kokotsomrong** - [Onpreyaq5](https://github.com/Onpreyaq5)
- **ศรัญ ธัญญวิกัย** - [hoh251](https://github.com/hoh251)
- **วิศรุต ขำหล่อ** - [wissarut-29](https://github.com/wissarut-29)
- **ชีวากร อาจดีลัง** - [cheewakornartdeelang](https://github.com/cheewakornartdeelang)