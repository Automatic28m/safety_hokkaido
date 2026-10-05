# 01_env — Environment & Requirements

## Runtime Environment
- Python 3.10+
- Dependencies: `requests`
- Standard Library: `json`, `re`, `threading`, `datetime`, `dataclasses`

## Environment Variables
Configured via `.env` or system environment:
- `METEOSOURCE_API_KEY`: API key for Meteosource Weather API (if not configured, gracefully returns `status="unavailable"`, `error_code="CONFIG_MISSING"`).
- `AVIATIONSTACK_API_KEY`: API key for AviationStack Flight API (if not configured, gracefully returns `status="unavailable"`, `error_code="CONFIG_MISSING"`).
- `ODPT_API_KEY`: Optional API key for Open Data for Public Transportation (ODPT) Japan. If not set, live transit status automatically uses Yahoo Transit Hokkaido live feed.
- `USE_LIVE_TRAIN`: Optional flag (defaults to live) to query real-time transit status.

## Adapters Structure (`external_data/`)
- `weather.py`: Real-time weather and hourly forecasts for Hokkaido cities (Meteosource).
- `disaster.py`: Real-time earthquakes and weather warnings from Japan Meteorological Agency (JMA).
- `trains.py`: Real-time train operation status for 24 Hokkaido lines (Yahoo Transit / ODPT API).
- `train.py`: Real-time JR Hokkaido train operational status adapter.
- `flights.py`: Flight arrival/departure status and blizzard delays for CTS New Chitose Airport (AviationStack).
- `roads.py`: Road conditions, expressways, and mountain pass closures in Hokkaido (Hokkaido Road Information).
- `cache.py`: Thread-safe in-memory `CacheStore` with TTL and stale cache support.
- `validation.py`: Input validation and sanitization for cities, regions, train lines, and airport codes.
- `tools.py`: Tool wrappers and schemas for LLM tool-calling interfaces.
