# 03_process — Architectural Scope & Safety Constraints

## Architectural Scope
This module supplies verified evidence, risk assessments, and route status. It acts as an objective knowledge and calculation provider.

## Critical Safety & Architectural Rules
1. **Evidence-Only Boundary:**
   - This module does not decide whether a user should travel or issue final traveler recommendations. The final deterministic action and natural language response belong strictly to Node 07 (`07_decision_llm_engine`).
2. **Relevance Score Interpretation:**
   - A low relevance score or empty search result indicates missing evidence; it must NEVER be interpreted as "conditions are safe".
3. **Conservative Failure Handling (Fail Conservatively):**
   - If indices are unavailable, corrupted, or cannot answer a query, return `degraded: true` with explanatory notices. Never fabricate success or assume safety when data is missing.
4. **Strict Provenance Preservation:**
   - Every returned chunk must maintain its source file name, 1-based page number (`page` and `page_number`), and version hash to guarantee end-to-end citation auditability.
5. **No AI Watermarks:**
   - All code, comments, and documentation must remain strictly professional without artificial intelligence watermarks or contributor labels.
