# 02_step — Execution Workflow

## Step-by-Step Processing Flow

1. **Receive Request:**
   - Parse `RetrievalRequest` containing the search query, `top_k`, and optional route/geo parameters.
2. **First-Stage Hybrid Retrieval:**
   - Run Dense Semantic Search against FAISS index (`document.index`) using embedded query vectors.
   - Run Sparse Lexical Search against BM25 index (`bm25_index.pkl`) using tokenized query terms.
   - Fuse candidate rankings using Reciprocal Rank Fusion (RRF, constant $k=60$).
3. **Second-Stage Re-Ranking:**
   - Pass top candidate chunks into the Cross-Encoder re-ranker.
   - Compute normalized relevance scores ($0.0 - 1.0$) and select final top-$k$ evidence chunks.
4. **Local Risk & Route Evaluation (Optional/Contextual):**
   - Ingest live weather, seismic, and transit data snapshots from module 04.
   - Evaluate risk criteria (wind speed, snow accumulation, seismic intensity, transit disruption) to assign a categorical risk level (`LOW`, `MEDIUM`, `HIGH`).
   - Identify closed highway segments or suspended transit corridors and determine alternative routes.
5. **Format & Return Response:**
   - Package output into `RiskKnowledgeResponse` preserving page provenance, source URLs, timestamps, and degraded mode status.
