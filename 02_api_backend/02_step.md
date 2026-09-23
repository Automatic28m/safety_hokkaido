# Request flow

1. `main.py` receives `POST /ask`.
2. The request schema carries the user message, chat history, and enabled tool switches.
3. The API delegates orchestration to `src.rag_pipeline.RAGPipeline` and returns its reply.

