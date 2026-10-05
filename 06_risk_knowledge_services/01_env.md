# 01_env — Environment & Requirements

## Runtime Environment
- Python 3.10 or newer (tested with Python 3.10 - 3.13)
- Pydantic v2 (for deterministic schema validation and contract serialization)
- FAISS (`faiss-cpu`) for dense vector search (L2 / Inner Product)
- rank-bm25 (`BM25Okapi`) for lexical search
- sentence-transformers (for embedding query encoding)
- Optional cross-encoder model for re-ranking (e.g. `BAAI/bge-reranker-base` or lightweight fallback)

## Upstream Dependencies
- `05_data_integration`: Vector index artifacts (`document.index`, `bm25_index.pkl`, `chunk_store.json`, `index_meta.json`)
- `04_external_data_services`: Live data snapshots (`LiveDataSnapshot`) for weather, disaster, and train status

## Downstream Consumers
- `07_decision_llm_engine`: Consumes ranked evidence chunks (`EvidenceChunk`), risk assessment (`RiskAssessment`), and route restrictions (`RouteInfo`)
- `03_travel_ai_agent`: Orchestrator issuing retrieval and risk queries
