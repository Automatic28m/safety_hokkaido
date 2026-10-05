import logging
import os
import re
from typing import Dict, Any, List, Optional

import requests

from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache, utc_now_iso
from external_data.validation import validate_line_name

logger = logging.getLogger(__name__)

YAHOO_TRAIN_PROVIDER = "yahoo_transit"
ODPT_TRAIN_PROVIDER = "odpt_public_transport"
TRAIN_KIND = "train"
DEFAULT_TRAIN_TTL = 300
REQUEST_TIMEOUT_SECONDS = 3.0
YAHOO_DIAINFO_HOKKAIDO_URL = "https://transit.yahoo.co.jp/diainfo/area/2"
ODPT_TRAIN_API_URL = "https://api.odpt.org/api/v4/odpt:TrainInformation"

# Map common English queries to Japanese line keywords
LINE_SEARCH_MAP = {
    "airport": ["エアポート", "千歳線"],
    "rapid airport": ["エアポート", "千歳線"],
    "chitose line": ["千歳線"],
    "chitose": ["千歳線"],
    "hakodate line": ["函館本線"],
    "hakodate": ["函館本線"],
    "muroran line": ["室蘭本線"],
    "muroran": ["室蘭本線"],
    "nemuro line": ["根室本線", "花咲線"],
    "nemuro": ["根室本線"],
    "sekisho line": ["石勝線"],
    "sekisho": ["石勝線"],
    "soya line": ["宗谷本線"],
    "soya": ["宗谷本線"],
    "sekihoku line": ["石北本線"],
    "sekihoku": ["石北本線"],
    "senmo line": ["釧網本線"],
    "senmo": ["釧網本線"],
    "furano line": ["富良野線"],
    "furano": ["富良野線"],
    "sassho line": ["札沼線", "学園都市線"],
    "sassho": ["札沼線"],
    "gakuentoshi line": ["学園都市線", "札沼線"],
    "gakuentoshi": ["学園都市線"],
    "hokkaido shinkansen": ["北海道新幹線", "新幹線"],
    "shinkansen": ["新幹線"],
}


def _parse_yahoo_transit_html(html_text: str) -> List[Dict[str, str]]:
    """Extract line status entries from Yahoo Transit Hokkaido HTML."""
    rows = re.findall(
        r'<tr>\s*<td><a[^>]*>(.*?)</a></td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>',
        html_text,
        re.DOTALL
    )
    results = []
    for line_col, status_col, detail_col in rows:
        clean_line = re.sub(r'<[^>]+>', '', line_col).strip()
        clean_status = re.sub(r'<[^>]+>', '', status_col).strip()
        clean_detail = re.sub(r'<[^>]+>', '', detail_col).strip()

        is_normal = "平常運転" in clean_status
        status_en = "normal" if is_normal else "delayed_or_suspended"

        results.append({
            "line_name": clean_line,
            "status_ja": clean_status,
            "status_en": status_en,
            "details": clean_detail
        })
    return results


def fetch_yahoo_transit_status(line_name: str = "All") -> LiveDataSnapshot:
    """Fetches live JR Hokkaido operational transit status from Yahoo Transit.
    
    Adheres strictly to the LiveDataSnapshot contract:
    - On success: status='ok'
    - On failure with cached data: status='stale'
    - On failure without cache: status='unavailable' with appropriate error_code
    """
    is_valid, valid_line, err_msg = validate_line_name(line_name)
    if not is_valid:
        return LiveDataSnapshot(
            provider=YAHOO_TRAIN_PROVIDER,
            kind=TRAIN_KIND,
            scope=str(line_name),
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="INVALID_INPUT",
            notice=err_msg,
            source_url=YAHOO_DIAINFO_HOKKAIDO_URL
        )

    # Check cache first
    cached = global_cache.get(YAHOO_TRAIN_PROVIDER, TRAIN_KIND, valid_line)
    if cached:
        return cached

    try:
        resp = requests.get(
            YAHOO_DIAINFO_HOKKAIDO_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SafetyHokkaido/1.0"},
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        if resp.status_code != 200:
            stale = global_cache.get_stale(YAHOO_TRAIN_PROVIDER, TRAIN_KIND, valid_line)
            if stale:
                return stale
            return LiveDataSnapshot(
                provider=YAHOO_TRAIN_PROVIDER,
                kind=TRAIN_KIND,
                scope=valid_line,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code=f"HTTP_{resp.status_code}",
                notice=f"Yahoo Transit returned HTTP {resp.status_code}.",
                source_url=YAHOO_DIAINFO_HOKKAIDO_URL
            )

        all_lines = _parse_yahoo_transit_html(resp.text)
        if not all_lines:
            stale = global_cache.get_stale(YAHOO_TRAIN_PROVIDER, TRAIN_KIND, valid_line)
            if stale:
                return stale
            return LiveDataSnapshot(
                provider=YAHOO_TRAIN_PROVIDER,
                kind=TRAIN_KIND,
                scope=valid_line,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code="PARSE_ERROR",
                notice="Could not parse any train lines from Yahoo Transit page.",
                source_url=YAHOO_DIAINFO_HOKKAIDO_URL
            )

        # Filter by line_name if not 'all'
        lower_line = valid_line.lower()
        if lower_line == "all":
            matched_lines = all_lines
        else:
            search_keywords = LINE_SEARCH_MAP.get(lower_line, [valid_line])
            matched_lines = [
                item for item in all_lines
                if any(kw in item["line_name"] for kw in search_keywords)
            ]
            if not matched_lines:
                # If specific section wasn't matched, keep all as context
                matched_lines = all_lines

        disrupted_lines = [i for i in matched_lines if i["status_en"] != "normal"]
        has_disruptions = len(disrupted_lines) > 0

        normalized_data = {
            "line_name": valid_line,
            "status": "disrupted" if has_disruptions else "normal",
            "is_delayed": has_disruptions,
            "queried_scope": valid_line,
            "total_lines_monitored": len(matched_lines),
            "disruptions_count": len(disrupted_lines),
            "has_disruptions": has_disruptions,
            "disrupted_lines": [
                {
                    "line_name": item["line_name"],
                    "status": item["status_ja"],
                    "details": item["details"]
                }
                for item in disrupted_lines
            ],
            "all_lines": matched_lines
        }

        notice = (
            f"Live JR Hokkaido status via Yahoo Transit: {len(disrupted_lines)} disruption(s) detected."
            if has_disruptions
            else "All monitored JR Hokkaido lines are running normally."
        )

        snapshot = LiveDataSnapshot(
            provider=YAHOO_TRAIN_PROVIDER,
            kind=TRAIN_KIND,
            scope=valid_line,
            status="ok",
            fetched_at=utc_now_iso(),
            data=normalized_data,
            source_url=YAHOO_DIAINFO_HOKKAIDO_URL,
            notice=notice
        )

        return global_cache.set(snapshot, ttl_seconds=DEFAULT_TRAIN_TTL)

    except requests.exceptions.Timeout:
        stale = global_cache.get_stale(YAHOO_TRAIN_PROVIDER, TRAIN_KIND, valid_line)
        if stale:
            stale.notice = f"Yahoo Transit request timed out; {stale.notice}"
            return stale
        return LiveDataSnapshot(
            provider=YAHOO_TRAIN_PROVIDER,
            kind=TRAIN_KIND,
            scope=valid_line,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="TIMEOUT",
            notice="Live train status request to Yahoo Transit timed out.",
            source_url=YAHOO_DIAINFO_HOKKAIDO_URL
        )
    except Exception as e:
        stale = global_cache.get_stale(YAHOO_TRAIN_PROVIDER, TRAIN_KIND, valid_line)
        if stale:
            return stale
        return LiveDataSnapshot(
            provider=YAHOO_TRAIN_PROVIDER,
            kind=TRAIN_KIND,
            scope=valid_line,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="FETCH_ERROR",
            notice=f"Failed to fetch Yahoo Transit live data: {str(e)}",
            source_url=YAHOO_DIAINFO_HOKKAIDO_URL
        )


def _normalize_odpt_response(items: List[Dict[str, Any]], valid_line: str) -> Dict[str, Any]:
    """Parses and normalizes raw ODPT train information items into standardized dictionary."""
    lower_line = valid_line.lower()
    if lower_line == "all":
        matched_items = items
    else:
        search_keywords = LINE_SEARCH_MAP.get(lower_line, [valid_line])
        matched_items = [
            it for it in items
            if any(kw.lower() in str(it.get("odpt:railway", "")).lower() or
                   kw in str(it.get("odpt:trainInformationText", ""))
                   for kw in search_keywords)
        ]
        if not matched_items:
            matched_items = items

    disrupted_lines = []
    for it in matched_items:
        raw_text = str(it.get("odpt:trainInformationText", ""))
        if "平常" not in raw_text and "normal" not in raw_text.lower():
            disrupted_lines.append({
                "line_name": it.get("odpt:railway", "Unknown"),
                "status_ja": raw_text,
                "status_en": "delayed_or_suspended",
                "details": raw_text
            })

    has_disruptions = len(disrupted_lines) > 0
    return {
        "line_name": valid_line,
        "status": "disrupted" if has_disruptions else "normal",
        "is_delayed": has_disruptions,
        "queried_scope": valid_line,
        "total_lines_monitored": len(matched_items),
        "disruptions_count": len(disrupted_lines),
        "has_disruptions": has_disruptions,
        "disrupted_lines": disrupted_lines,
    }


def _fetch_odpt_train_status(valid_line: str, api_key: str) -> Optional[LiveDataSnapshot]:
    """Attempts to query the Open Data for Public Transportation (ODPT) API using ODPT_API_KEY."""
    if not api_key:
        return None
    try:
        cached = global_cache.get(ODPT_TRAIN_PROVIDER, TRAIN_KIND, valid_line)
        if cached:
            return cached

        url = f"{ODPT_TRAIN_API_URL}?acl:consumerKey={api_key}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list) and len(items) > 0:
                normalized_data = _normalize_odpt_response(items, valid_line)
                snap = LiveDataSnapshot(
                    provider=ODPT_TRAIN_PROVIDER,
                    kind=TRAIN_KIND,
                    scope=valid_line,
                    status="ok",
                    fetched_at=utc_now_iso(),
                    data=normalized_data,
                    source_url="https://developer.odpt.org/",
                    notice="Live operational status from ODPT Public Transportation Open Data API."
                )
                return global_cache.set(snap, ttl_seconds=DEFAULT_TRAIN_TTL)
    except Exception as e:
        logger.debug("Failed to fetch ODPT train status: %s", e)
        return None
    return None


def fetch_live_train_status(line_name: str = "All") -> LiveDataSnapshot:
    """Unified entry point for live train status.
    
    1. Checks USE_LIVE_TRAIN flag (returns unavailable if explicitly disabled).
    2. Validates input line name.
    3. If ODPT_API_KEY is configured, checks the ODPT Open Data API.
    4. Otherwise (or on ODPT miss/error), checks Yahoo Transit Hokkaido live feed.
    """
    use_live = os.getenv("USE_LIVE_TRAIN", "true").strip().lower()
    if use_live in ("false", "0", "no"):
        return LiveDataSnapshot(
            provider="train_adapter",
            kind=TRAIN_KIND,
            scope=str(line_name),
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="LIVE_TRAIN_DISABLED",
            notice="Live train status checking is disabled via USE_LIVE_TRAIN environment variable.",
            source_url=YAHOO_DIAINFO_HOKKAIDO_URL
        )

    is_valid, valid_line, err_msg = validate_line_name(line_name)
    if not is_valid:
        return LiveDataSnapshot(
            provider="train_adapter",
            kind=TRAIN_KIND,
            scope=str(line_name),
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="INVALID_INPUT",
            notice=err_msg,
            source_url=YAHOO_DIAINFO_HOKKAIDO_URL
        )

    odpt_key = os.getenv("ODPT_API_KEY", "").strip()
    if odpt_key:
        odpt_snap = _fetch_odpt_train_status(valid_line, odpt_key)
        if odpt_snap and odpt_snap.status == "ok":
            return odpt_snap

    return fetch_yahoo_transit_status(valid_line)
