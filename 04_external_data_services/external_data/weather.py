import requests
from typing import Optional
from config import config
from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache, utc_now_iso
from external_data.validation import validate_city

WEATHER_PROVIDER = "meteosource"
WEATHER_KIND = "weather"
DEFAULT_WEATHER_TTL = 600
REQUEST_TIMEOUT_SECONDS = 5.0
SOURCE_PORTAL_URL = "https://www.meteosource.com"


def fetch_real_time_weather(city_name: str) -> LiveDataSnapshot:
    is_valid, valid_city, err_msg = validate_city(city_name)
    if not is_valid:
        return LiveDataSnapshot(
            provider=WEATHER_PROVIDER,
            kind=WEATHER_KIND,
            scope=str(city_name),
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="INVALID_INPUT",
            notice=err_msg,
            source_url=SOURCE_PORTAL_URL
        )

    cached = global_cache.get(WEATHER_PROVIDER, WEATHER_KIND, valid_city)
    if cached:
        return cached

    api_key = getattr(config, "METEOSOURCE_API_KEY", "")
    if not api_key:
        stale = global_cache.get_stale(WEATHER_PROVIDER, WEATHER_KIND, valid_city)
        if stale:
            stale.notice = "METEOSOURCE_API_KEY is not configured; serving stale cache."
            return stale
        return LiveDataSnapshot(
            provider=WEATHER_PROVIDER,
            kind=WEATHER_KIND,
            scope=valid_city,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="CONFIG_MISSING",
            notice="Weather service is unavailable because METEOSOURCE_API_KEY is not configured.",
            source_url=SOURCE_PORTAL_URL
        )

    try:
        find_url = "https://www.meteosource.com/api/v1/free/find_places_prefix"
        find_resp = requests.get(
            find_url,
            params={"text": valid_city, "key": api_key},
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        if find_resp.status_code != 200:
            stale = global_cache.get_stale(WEATHER_PROVIDER, WEATHER_KIND, valid_city)
            if stale:
                return stale
            return LiveDataSnapshot(
                provider=WEATHER_PROVIDER,
                kind=WEATHER_KIND,
                scope=valid_city,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code=f"HTTP_{find_resp.status_code}",
                notice=f"Meteosource place search returned HTTP {find_resp.status_code}.",
                source_url=SOURCE_PORTAL_URL
            )

        places = find_resp.json()
        if not places or not isinstance(places, list):
            return LiveDataSnapshot(
                provider=WEATHER_PROVIDER,
                kind=WEATHER_KIND,
                scope=valid_city,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code="CITY_NOT_FOUND",
                notice=f"No matching location found for city '{valid_city}'.",
                source_url=SOURCE_PORTAL_URL
            )

        target_place = places[0]
        place_id = target_place.get("place_id")
        place_name = target_place.get("name", valid_city)
        country = target_place.get("country")
        lat = target_place.get("lat")
        lon = target_place.get("lon")

        weather_url = "https://www.meteosource.com/api/v1/free/point"
        weather_resp = requests.get(
            weather_url,
            params={
                "place_id": place_id,
                "sections": "all",
                "timezone": "UTC",
                "language": "en",
                "units": "metric",
                "key": api_key
            },
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        if weather_resp.status_code != 200:
            stale = global_cache.get_stale(WEATHER_PROVIDER, WEATHER_KIND, valid_city)
            if stale:
                return stale
            return LiveDataSnapshot(
                provider=WEATHER_PROVIDER,
                kind=WEATHER_KIND,
                scope=valid_city,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code=f"HTTP_{weather_resp.status_code}",
                notice=f"Meteosource weather point query returned HTTP {weather_resp.status_code}.",
                source_url=SOURCE_PORTAL_URL
            )

        weather_json = weather_resp.json()
        current = weather_json.get("current")
        hourly_raw = weather_json.get("hourly", {}).get("data", [])
        hourly_data = hourly_raw[:24] if isinstance(hourly_raw, list) else []

        if not current:
            return LiveDataSnapshot(
                provider=WEATHER_PROVIDER,
                kind=WEATHER_KIND,
                scope=valid_city,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code="MALFORMED_RESPONSE",
                notice="Meteosource response missing current weather section.",
                source_url=SOURCE_PORTAL_URL
            )

        status = "ok" if hourly_data else "partial"
        normalized_data = {
            "place_id": place_id,
            "city_name": place_name,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "current": {
                "temperature_c": current.get("temperature"),
                "summary": current.get("summary"),
                "icon_num": current.get("icon_num"),
                "wind_speed_ms": current.get("wind", {}).get("speed") if isinstance(current.get("wind"), dict) else None,
                "wind_angle_deg": current.get("wind", {}).get("angle") if isinstance(current.get("wind"), dict) else None,
                "wind_dir": current.get("wind", {}).get("dir") if isinstance(current.get("wind"), dict) else None,
                "precipitation_total_mm": current.get("precipitation", {}).get("total") if isinstance(current.get("precipitation"), dict) else None,
                "precipitation_type": current.get("precipitation", {}).get("type") if isinstance(current.get("precipitation"), dict) else None,
                "cloud_cover_pct": current.get("cloud_cover")
            },
            "hourly_forecast": [
                {
                    "time_utc": h.get("date"),
                    "temperature_c": h.get("temperature"),
                    "summary": h.get("summary"),
                    "precipitation_total_mm": h.get("precipitation", {}).get("total") if isinstance(h.get("precipitation"), dict) else None
                }
                for h in hourly_data if isinstance(h, dict)
            ]
        }

        snapshot = LiveDataSnapshot(
            provider=WEATHER_PROVIDER,
            kind=WEATHER_KIND,
            scope=valid_city,
            status=status,
            fetched_at=utc_now_iso(),
            data=normalized_data,
            source_url=SOURCE_PORTAL_URL,
            notice="Weather snapshot successfully retrieved." if status == "ok" else "Weather forecast missing hourly data."
        )

        return global_cache.set(snapshot, ttl_seconds=DEFAULT_WEATHER_TTL)

    except requests.exceptions.Timeout:
        stale = global_cache.get_stale(WEATHER_PROVIDER, WEATHER_KIND, valid_city)
        if stale:
            return stale
        return LiveDataSnapshot(
            provider=WEATHER_PROVIDER,
            kind=WEATHER_KIND,
            scope=valid_city,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="TIMEOUT",
            notice="Connection to Meteosource timed out.",
            source_url=SOURCE_PORTAL_URL
        )
    except requests.exceptions.RequestException as e:
        stale = global_cache.get_stale(WEATHER_PROVIDER, WEATHER_KIND, valid_city)
        if stale:
            return stale
        return LiveDataSnapshot(
            provider=WEATHER_PROVIDER,
            kind=WEATHER_KIND,
            scope=valid_city,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="CONNECTION_ERROR",
            notice=f"Network error communicating with Meteosource: {str(e)}",
            source_url=SOURCE_PORTAL_URL
        )
    except Exception as e:
        stale = global_cache.get_stale(WEATHER_PROVIDER, WEATHER_KIND, valid_city)
        if stale:
            return stale
        return LiveDataSnapshot(
            provider=WEATHER_PROVIDER,
            kind=WEATHER_KIND,
            scope=valid_city,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="PROCESSING_ERROR",
            notice=f"Unexpected error while processing weather data: {str(e)}",
            source_url=SOURCE_PORTAL_URL
        )
