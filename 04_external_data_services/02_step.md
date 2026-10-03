# 02_step — Adapter Flow

1. **Input Validation:** Validate input parameters via `validation.py` (city, region, train line, airport code). Reject invalid or unsafe inputs with `status="unavailable"`, `error_code="INVALID_INPUT"`.
2. **Cache Inspection:** Check `global_cache` for active non-expired `LiveDataSnapshot`. If present, return cached snapshot immediately.
3. **Live Fetch:** If cache miss, invoke external provider endpoint with strict timeout (3.0s – 4.0s).
4. **Data Normalization:** Parse and normalize external payload into a standard `LiveDataSnapshot` with `status="ok"` and save to cache with appropriate TTL.
5. **Fault Tolerance & Fallback:**
   - On provider network failure or timeout: serve expired cached data marked as `status="stale"` if available.
   - If no cache exists: return `status="unavailable"` with explicit `error_code` (e.g. `TIMEOUT`, `CONFIG_MISSING`, `HTTP_ERR`) and helpful notice.
