import requests
from typing import Dict, Any, List, Optional
from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache, utc_now_iso
from external_data.validation import validate_region

DISASTER_PROVIDER = "jma"
DISASTER_KIND = "disaster"
DEFAULT_DISASTER_TTL = 300
REQUEST_TIMEOUT_SECONDS = 5.0
JMA_QUAKE_URL = "https://www.jma.go.jp/bosai/quake/data/list.json"
JMA_QUAKE_SOURCE = "https://www.jma.go.jp/bosai/quake/"
JMA_WARNING_SOURCE = "https://www.jma.go.jp/bosai/warning/"

# Major JMA Hokkaido meteorological offices
HOKKAIDO_OFFICES = {
    "016000": "Ishikari, Sorachi, Shiribeshi (including Sapporo)",
    "012000": "Kamikawa, Rumoi (including Asahikawa)",
    "017000": "Oshima, Hiyama (including Hakodate)",
    "014030": "Tokachi (including Obihiro)",
    "013000": "Abashiri, Kitami, Mombetsu",
    "011000": "Soya (including Wakkanai)",
    "015000": "Iburi, Hidaka",
    "014100": "Kushiro, Nemuro"
}


import re

HOKKAIDO_JA_KEYWORDS = [
    "北海道", "十勝", "石狩", "渡島", "檜山", "後志", "空知", "上川",
    "留萌", "宗谷", "オホーツク", "網走", "北見", "紋別", "胆振", "日高",
    "釧路", "根室"
]

# Regex with word boundaries for English names
HOKKAIDO_EN_REGEX = re.compile(
    r"\b(hokkaido|tokachi|ishikari|oshima|hiyama|shiribeshi|sorachi|kamikawa|rumoi|soya|abashiri|kitami|mombetsu|iburi|hidaka|kushiro|nemuro)\b",
    re.IGNORECASE
)


def _fetch_earthquake_data() -> Tuple_Quake_Result:
    # Internal fetcher for JMA earthquake list
    resp = requests.get(JMA_QUAKE_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    if resp.status_code != 200:
        return False, None, f"HTTP {resp.status_code}"
    
    quakes_json = resp.json()
    if not isinstance(quakes_json, list):
        return False, None, "Malformed earthquake feed"

    hokkaido_quakes = []
    for q in quakes_json:
        anm = q.get("anm", "")
        en_anm = q.get("en_anm", "")
        
        # Exclude Amami-Oshima, Hiroshima, Kagoshima false matches
        if "奄美" in anm or "広島" in anm or "鹿児島" in anm:
            continue
        if "amami" in en_anm.lower() or "hiroshima" in en_anm.lower() or "kagoshima" in en_anm.lower():
            continue

        is_hokkaido = (
            any(kw in anm for kw in HOKKAIDO_JA_KEYWORDS) or
            bool(HOKKAIDO_EN_REGEX.search(en_anm))
        )

        if is_hokkaido:
            hokkaido_quakes.append({
                "time_jst": q.get("rdt"),
                "epicenter_en": en_anm or "Hokkaido area",
                "epicenter_ja": anm,
                "magnitude": q.get("mag"),
                "max_intensity": q.get("maxi"),
                "coordinates": q.get("cod")
            })

    return True, hokkaido_quakes, None


def _fetch_office_warnings(office_code: str) -> Tuple_Warning_Result:
    # Internal fetcher for JMA bosai weather warnings
    url = f"https://www.jma.go.jp/bosai/warning/data/warning/{office_code}.json"
    resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    if resp.status_code != 200:
        return False, None, f"HTTP {resp.status_code}"

    warn_json = resp.json()
    if not isinstance(warn_json, dict):
        return False, None, "Malformed warning feed"

    headline = warn_json.get("headlineText")
    report_datetime = warn_json.get("reportDatetime")

    return True, {
        "office_code": office_code,
        "office_name": HOKKAIDO_OFFICES.get(office_code, office_code),
        "report_datetime": report_datetime,
        "headline": headline if headline else None
    }, None


Tuple_Quake_Result = Any
Tuple_Warning_Result = Any


def fetch_disaster_warnings(region: str = "Hokkaido") -> LiveDataSnapshot:
    is_valid, valid_region, err_msg = validate_region(region)
    if not is_valid:
        return LiveDataSnapshot(
            provider=DISASTER_PROVIDER,
            kind=DISASTER_KIND,
            scope=str(region),
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="INVALID_INPUT",
            notice=err_msg,
            source_url=JMA_QUAKE_SOURCE
        )

    cached = global_cache.get(DISASTER_PROVIDER, DISASTER_KIND, valid_region)
    if cached:
        return cached

    quake_ok = False
    quake_data = None
    quake_err = None

    warning_ok = False
    warning_data = None
    warning_err = None

    # 1. Fetch live earthquake data
    try:
        quake_ok, quake_data, quake_err = _fetch_earthquake_data()
    except requests.exceptions.Timeout:
        quake_err = "TIMEOUT"
    except requests.exceptions.RequestException as e:
        quake_err = f"CONNECTION_ERROR: {str(e)}"
    except Exception as e:
        quake_err = f"PROCESSING_ERROR: {str(e)}"

    # 2. Fetch live meteorological warning data (Primary: Sapporo/Ishikari office 016000)
    target_office = "016000"
    region_lower = valid_region.lower()
    if "hakodate" in region_lower or "oshima" in region_lower:
        target_office = "017000"
    elif "asahikawa" in region_lower or "kamikawa" in region_lower:
        target_office = "012000"
    elif "obihiro" in region_lower or "tokachi" in region_lower:
        target_office = "014030"
    elif "kushiro" in region_lower or "nemuro" in region_lower:
        target_office = "014100"
    elif "wakkanai" in region_lower or "soya" in region_lower:
        target_office = "011000"
    elif "kitami" in region_lower or "abashiri" in region_lower:
        target_office = "013000"

    try:
        warning_ok, warning_data, warning_err = _fetch_office_warnings(target_office)
    except requests.exceptions.Timeout:
        warning_err = "TIMEOUT"
    except requests.exceptions.RequestException as e:
        warning_err = f"CONNECTION_ERROR: {str(e)}"
    except Exception as e:
        warning_err = f"PROCESSING_ERROR: {str(e)}"

    # Check overall outcome
    if not quake_ok and not warning_ok:
        # Both failed: return stale cache or unavailable
        stale = global_cache.get_stale(DISASTER_PROVIDER, DISASTER_KIND, valid_region)
        if stale:
            return stale
        return LiveDataSnapshot(
            provider=DISASTER_PROVIDER,
            kind=DISASTER_KIND,
            scope=valid_region,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="PROVIDER_UNAVAILABLE",
            notice=f"Failed to fetch live JMA disaster feeds (Earthquake: {quake_err}, Warnings: {warning_err}).",
            source_url=JMA_QUAKE_SOURCE
        )

    # Determine status: ok if both succeed, unavailable if at least one fails
    if quake_ok and warning_ok:
        status = "ok"
    else:
        # At least one provider failed -> treat as unavailable
        status = "unavailable"

    notices = []
    if quake_ok and not warning_ok:
        notices.append("Earthquake data available")
        notices.append(f"Weather warning feed unavailable ({warning_err})")
    elif not quake_ok and warning_ok:
        notices.append("Weather warnings available")
        notices.append(f"Earthquake feed unavailable ({quake_err})")

    normalized_data = {
        "region_scope": valid_region,
        "earthquakes": {
            "is_available": quake_ok,
            "recent_hokkaido_events": quake_data if quake_ok else [],
            "count": len(quake_data) if (quake_ok and quake_data) else 0,
            "latest_event": quake_data[0] if (quake_ok and quake_data) else None
        },
        "meteorological_warnings": {
            "is_available": warning_ok,
            "jurisdiction": HOKKAIDO_OFFICES.get(target_office),
            "office_code": target_office,
            "active_headline": warning_data.get("headline") if (warning_ok and warning_data) else None,
            "report_datetime": warning_data.get("report_datetime") if (warning_ok and warning_data) else None
        }
    }

    notice_str = "; ".join(notices) if notices else "JMA disaster and warning feeds active."

    snapshot = LiveDataSnapshot(
        provider=DISASTER_PROVIDER,
        kind=DISASTER_KIND,
        scope=valid_region,
        status=status,
        fetched_at=utc_now_iso(),
        data=normalized_data,
        source_url=f"{JMA_QUAKE_SOURCE} and {JMA_WARNING_SOURCE}",
        notice=notice_str
    )

    if status == "ok":
        return global_cache.set(snapshot, ttl_seconds=DEFAULT_DISASTER_TTL)
    return snapshot
