# Data flow

1. Load vetted PDFs and JSON documents from `02_api_backend/data/`.
2. Split text, embed chunks, and persist index metadata.
3. Retain source name and page/chunk provenance with every indexed record.
