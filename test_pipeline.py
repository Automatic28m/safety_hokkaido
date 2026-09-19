from src.rag_pipeline import RAGPipeline
pipeline = RAGPipeline()
print(pipeline.ask("What is the weather in Sapporo?", use_agent=False))
