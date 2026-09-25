# Safety Hokkaido Architecture Strict Guidelines

## 01_web_app
- รับผิดชอบเฉพาะ UI ไม่ตัดสิน safety เอง
- ห้ามซ่อนสถานะ unavailable/stale/mocked จาก API
- ห้าม hard-code API key ลง browser

## 02_api_backend
- ไม่ return error ใน `reply` พร้อม HTTP 200 (ต้องใช้ 400/500/503)
- ห้ามวาง orchestration, retrieval หรือ LLM decision ใน FastAPI route

## 03_travel_ai_agent
- ห้ามใช้ `global_memory` ต้องผูกกับ `conversation_id`
- โมดูล 03 เป็นผู้เลือก Tool และเรียกใช้ API (Node 04) แทน Node 07
- ห้ามให้ generator (Node 07) เรียก provider โดยตรง

## 04_external_data_services
- คืน `LiveDataSnapshot` พร้อมสถานะ ok/unavailable/stale/mocked
- ห้าม fabricate success จาก provider failure

## 05_data_integration
- ทำ Index จาก PDF ต้องระบุเลขหน้า
- ห้ามเปลี่ยน field เดิมของ chunk จน generator รุ่นเก่าพัง

## 06_risk_knowledge_services
- ห้ามสร้างหรือสรุป official warning เอง
- ห้ามนำ relevance score ต่ำไปตีความว่า “ปลอดภัย”

## 07_decision_llm_engine
- ห้ามเรียก external provider / network tool เองเด็ดขาด!
- โมดูล 07 มีหน้าที่รับ Evidence ที่ตรวจสอบแล้วจาก Node 03 เพื่อสร้างคำตอบที่ grounded
- ถ้าข้อมูลไม่พอ ห้ามสรุปว่า Safe
- คืน `reply`, `safety_level`, `used_evidence_ids`, `used_live_sources`, `degraded`, `notices`
- Output ต้องเป็น Markdown ไม่มี HTML/JS

## 08_recommendation_feedback
- ห้าม auto-train หรือ auto-change guardrail จาก feedback ผู้ใช้
- ห้ามใช้ feedback ปรับพฤติกรรมโดยไม่มี Human review

**CRITICAL RULE:** ห้ามมี AI watermark หรือ AI contributor ในงานที่ส่งขึ้น GitHub เด็ดขาด!
