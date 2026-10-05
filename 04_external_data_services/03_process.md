# 03_process — Source Policy & Safety Rules

1. **Source Policy:**
   - Weather: Meteosource API (`weather.py`)
   - Disaster: Japan Meteorological Agency (JMA Bosai) official feeds (`disaster.py`)
   - Transit: Yahoo Transit live service information and ODPT API (`trains.py`, `train.py`)
   - Flights: AviationStack flight tracking for Hokkaido airports (`flights.py`)
   - Roads: Hokkaido Road Information system (`roads.py`)

2. **Strict Architecture & Safety Contracts:**
   - **Contract Compliance:** Every adapter MUST return a `LiveDataSnapshot` with `status` strictly set to one of `ok`, `unavailable`, `stale`, or `mocked`.
   - **No Fabricated Success:** Never fabricate success from provider failure.
   - **No Safety Decisions:** Node 04 is strictly a data provider. Never make safety judgments, output `safety_level`, or make evacuation recommendations (safety synthesis is strictly the responsibility of Node 07).
