import os
import requests
from typing import Dict, Any, List, Optional
from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache, utc_now_iso
from external_data.validation import validate_airport_code

FLIGHT_PROVIDER = "aviationstack"
FLIGHT_KIND = "flight"
DEFAULT_FLIGHT_TTL = 1800  # 30 minutes caching to aggressively protect 100 req/mo quota
REQUEST_TIMEOUT_SECONDS = 4.0
# NOTE: AviationStack free tier does NOT support HTTPS; HTTP is required
AVIATIONSTACK_API_URL = "http://api.aviationstack.com/v1/flights"
SOURCE_PORTAL_URL = "https://aviationstack.com"


def _get_api_key() -> str:
    key = os.getenv("AVIATIONSTACK_API_KEY", "")
    if key:
        return key.strip()
    try:
        from config import config
        return getattr(config, "AVIATIONSTACK_API_KEY", "").strip()
    except Exception:
        return ""


def fetch_flight_status(airport_code: str = "CTS", direction: str = "arrival") -> LiveDataSnapshot:
    """Fetches real-time flight arrival/departure status for Hokkaido airports (default: New Chitose CTS).
    direction can be 'arrival', 'departure', or 'both'.
    """
    is_valid, valid_airport, err_msg = validate_airport_code(airport_code)
    if not is_valid:
        return LiveDataSnapshot(
            provider=FLIGHT_PROVIDER,
            kind=FLIGHT_KIND,
            scope=f"{airport_code}_{direction}",
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="INVALID_INPUT",
            notice=err_msg,
            source_url=SOURCE_PORTAL_URL
        )

    # If both, fetch separately and merge to fully utilize cache efficiency
    if direction == "both":
        arr_snap = fetch_flight_status(valid_airport, "arrival")
        dep_snap = fetch_flight_status(valid_airport, "departure")
        
        # Merge data gracefully
        arr_data = arr_snap.data.get("flights", []) if arr_snap.data else []
        dep_data = dep_snap.data.get("flights", []) if dep_snap.data else []
        combined_flights = arr_data + dep_data
        
        delays = sum(1 for f in combined_flights if f.get("delay_minutes", 0) and f.get("delay_minutes", 0) > 15)
        cancels = sum(1 for f in combined_flights if f.get("flight_status") == "cancelled")
        
        return LiveDataSnapshot(
            provider=FLIGHT_PROVIDER,
            kind=FLIGHT_KIND,
            scope=f"{valid_airport}_both",
            status="ok" if arr_snap.status == "ok" or dep_snap.status == "ok" else arr_snap.status,
            fetched_at=utc_now_iso(),
            data={
                "airport_code": valid_airport,
                "total_flights": len(combined_flights),
                "delayed_count": delays,
                "cancelled_count": cancels,
                "has_major_disruption": (cancels > 0 or delays > 2),
                "flights": combined_flights
            },
            notice=f"Merged {len(arr_data)} arrivals and {len(dep_data)} departures for {valid_airport}",
            source_url=SOURCE_PORTAL_URL
        )

    scope_key = f"{valid_airport}_{direction}"
    
    # Check cache first
    cached = global_cache.get(FLIGHT_PROVIDER, FLIGHT_KIND, scope_key)
    if cached:
        return cached

    api_key = _get_api_key()
    if not api_key:
        stale = global_cache.get_stale(FLIGHT_PROVIDER, FLIGHT_KIND, scope_key)
        if stale:
            stale.notice = "AVIATIONSTACK_API_KEY is not configured; serving stale cache."
            return stale
        return LiveDataSnapshot(
            provider=FLIGHT_PROVIDER,
            kind=FLIGHT_KIND,
            scope=scope_key,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="CONFIG_MISSING",
            notice="Flight service is unavailable because AVIATIONSTACK_API_KEY is not configured.",
            source_url=SOURCE_PORTAL_URL
        )

    try:
        params = {
            "access_key": api_key,
            "limit": 15
        }
        if direction == "departure":
            params["dep_iata"] = valid_airport
        else:
            params["arr_iata"] = valid_airport
            
        resp = requests.get(
            AVIATIONSTACK_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        if resp.status_code != 200:
            stale = global_cache.get_stale(FLIGHT_PROVIDER, FLIGHT_KIND, scope_key)
            if stale:
                return stale
            return LiveDataSnapshot(
                provider=FLIGHT_PROVIDER,
                kind=FLIGHT_KIND,
                scope=scope_key,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code=f"HTTP_{resp.status_code}",
                notice=f"AviationStack API returned HTTP {resp.status_code}.",
                source_url=SOURCE_PORTAL_URL
            )

        payload = resp.json()

        # Handle API-level errors
        if "error" in payload:
            err = payload["error"]
            err_code = str(err.get("code", "API_ERROR")).upper()
            err_info = err.get("info", "AviationStack returned an error.")
            stale = global_cache.get_stale(FLIGHT_PROVIDER, FLIGHT_KIND, scope_key)
            if stale:
                stale.notice = f"AviationStack error ({err_code}); {stale.notice}"
                return stale
            return LiveDataSnapshot(
                provider=FLIGHT_PROVIDER,
                kind=FLIGHT_KIND,
                scope=scope_key,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code=err_code,
                notice=err_info,
                source_url=SOURCE_PORTAL_URL
            )

        raw_flights = payload.get("data", [])
        normalized_flights = []
        delayed_count = 0
        cancelled_count = 0

        for f in raw_flights:
            status = f.get("flight_status", "unknown")
            delay = f.get(direction, {}).get("delay") # Use arrival or departure block based on direction
            if not delay:
                # Fallback to the other block just in case API returns it differently
                other = "departure" if direction == "arrival" else "arrival"
                delay = f.get(other, {}).get("delay")
                
            if status == "cancelled":
                cancelled_count += 1
            elif delay and delay > 15:
                delayed_count += 1

            normalized_flights.append({
                "direction": direction,
                "flight_number": f.get("flight", {}).get("iata"),
                "airline": f.get("airline", {}).get("name"),
                "flight_status": status,
                "departure_airport": f.get("departure", {}).get("airport"),
                "departure_iata": f.get("departure", {}).get("iata"),
                "arrival_airport": f.get("arrival", {}).get("airport"),
                "arrival_iata": f.get("arrival", {}).get("iata"),
                "scheduled_time": f.get(direction, {}).get("scheduled"),
                "estimated_time": f.get(direction, {}).get("estimated"),
                "delay_minutes": delay
            })

        has_major_disruption = (cancelled_count > 0) or (delayed_count > 2)
        normalized_data = {
            "airport_code": valid_airport,
            "direction": direction,
            "total_flights": len(normalized_flights),
            "delayed_count": delayed_count,
            "cancelled_count": cancelled_count,
            "has_major_disruption": has_major_disruption,
            "flights": normalized_flights
        }

        notice = (
            f"Airport {valid_airport} ({direction}) flight status: {cancelled_count} cancelled, {delayed_count} delayed."
            if has_major_disruption
            else f"Flights operating normally at {valid_airport} ({direction})."
        )

        snapshot = LiveDataSnapshot(
            provider=FLIGHT_PROVIDER,
            kind=FLIGHT_KIND,
            scope=scope_key,
            status="ok",
            fetched_at=utc_now_iso(),
            data=normalized_data,
            source_url=SOURCE_PORTAL_URL,
            notice=notice
        )

        return global_cache.set(snapshot, ttl_seconds=DEFAULT_FLIGHT_TTL)

    except requests.exceptions.Timeout:
        stale = global_cache.get_stale(FLIGHT_PROVIDER, FLIGHT_KIND, scope_key)
        if stale:
            stale.notice = f"AviationStack timed out; {stale.notice}"
            return stale
        return LiveDataSnapshot(
            provider=FLIGHT_PROVIDER,
            kind=FLIGHT_KIND,
            scope=scope_key,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="TIMEOUT",
            notice=f"Flight status request to AviationStack for '{scope_key}' timed out.",
            source_url=SOURCE_PORTAL_URL
        )
    except Exception as e:
        stale = global_cache.get_stale(FLIGHT_PROVIDER, FLIGHT_KIND, scope_key)
        if stale:
            return stale
        return LiveDataSnapshot(
            provider=FLIGHT_PROVIDER,
            kind=FLIGHT_KIND,
            scope=scope_key,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="FETCH_ERROR",
            notice=f"Failed to fetch flight data: {str(e)}",
            source_url=SOURCE_PORTAL_URL
        )
