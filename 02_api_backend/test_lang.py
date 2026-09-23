from src.rag_pipeline import RAGPipeline
rag = RAGPipeline()
rag.ask("สวัสดี")
print("Response 1:", rag.ask("ตอนนี้สภาพอากาศที่นิเซโกะเป็นอย่างไรบ้าง?"))
print("Response 2:", rag.ask("แล้วฉันควรเตรียมเสื้อผ้าแบบไหนไปที่นั่น?"))
