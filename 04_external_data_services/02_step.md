# Adapter flow

1. Validate tool input and call the provider with timeouts.
2. Normalize results into a small, cited data snapshot.
3. Return an explicit unavailable/degraded result if the provider fails.
