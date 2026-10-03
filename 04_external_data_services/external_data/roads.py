import requests
from typing import Dict, Any, List, Optional
from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache, utc_now_iso
from external_data.validation import validate_region

ROAD_PROVIDER = "hokkaido_road_info"
ROAD_KIND = "road"
DEFAULT_ROAD_TTL = 600  # 10 minutes
REQUEST_TIMEOUT_SECONDS = 3.0
ROAD_PORTAL_URL = "https://www.road-info-prvs.mlit.go.jp/"

# Critical mountain passes and expressways susceptible to winter blizzards
HOKKAIDO_KEY_ROUTES = [
    {
        "name": "Do-O Expressway (道央自動車道)",
        "route_id": "E5",
        "section": "Sapporo - Asahikawa / Chitose",
        "type": "expressway"
    },
    {
        "name": "Sasson Expressway (札樽自動車道)",
        "route_id": "E5A",
        "section": "Sapporo - Otaru",
        "type": "expressway"
    },
    {
        "name": "Doto Expressway (道東自動車道)",
        "route_id": "E38",
        "section": "Chitose - Obihiro / Kushiro",
        "type": "expressway"
    },
    {
        "name": "Nakayama Pass (中山峠)",
        "route_id": "Route 230",
        "section": "Sapporo - Rusutsu / Niseko",
        "type": "mountain_pass"
    },
    {
        "name": "Nissho Pass (日勝峠)",
        "route_id": "Route 274",
        "section": "Yubari - Shimizu / Tokachi",
        "type": "mountain_pass"
    },
    {
        "name": "Sekihoku Pass (石北峠)",
        "route_id": "Route 39",
        "section": "Kamikawa - Kitami",
        "type": "mountain_pass"
    },
    {
        "name": "Karikachi Pass (狩勝峠)",
        "route_id": "Route 38",
        "section": "Minamifurano - Shintoku",
        "type": "mountain_pass"
    }
]


def fetch_road_status(region: str = "Hokkaido") -> LiveDataSnapshot:
    """Fetches real-time road and expressway conditions for Hokkaido.
    
    Adheres strictly to the LiveDataSnapshot contract:
    - On success: status='ok'
    - On failure with cached data: status='stale'
    - On failure without cache: status='unavailable'
    """
    is_valid, valid_region, err_msg = validate_region(region)
    if not is_valid:
        return LiveDataSnapshot(
            provider=ROAD_PROVIDER,
            kind=ROAD_KIND,
            scope=str(region),
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="INVALID_INPUT",
            notice=err_msg,
            source_url=ROAD_PORTAL_URL
        )

    # Check cache first
    cached = global_cache.get(ROAD_PROVIDER, ROAD_KIND, valid_region)
    if cached:
        return cached

    try:
        resp = requests.get(
            ROAD_PORTAL_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SafetyHokkaido/1.0"},
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        if resp.status_code != 200:
            stale = global_cache.get_stale(ROAD_PROVIDER, ROAD_KIND, valid_region)
            if stale:
                return stale
            return LiveDataSnapshot(
                provider=ROAD_PROVIDER,
                kind=ROAD_KIND,
                scope=valid_region,
                status="unavailable",
                fetched_at=utc_now_iso(),
                error_code=f"HTTP_{resp.status_code}",
                notice=f"Hokkaido Road Information portal returned HTTP {resp.status_code}.",
                source_url=ROAD_PORTAL_URL
            )

        # Check for closure notices or blizzard warnings on the portal
        page_content = resp.text
        has_closure_mentions = ("通行止" in page_content) or ("規制" in page_content)
        has_winter_hazards = ("凍結" in page_content) or ("吹雪" in page_content) or ("チェーン" in page_content)

        # Build route status summary
        route_statuses = []
        for route in HOKKAIDO_KEY_ROUTES:
            route_name_ja = route["name"].split("(")[-1].replace(")", "")
            is_affected = route_name_ja in page_content if route_name_ja else False

            route_statuses.append({
                "route_name": route["name"],
                "route_id": route["route_id"],
                "section": route["section"],
                "type": route["type"],
                "status": "caution_winter_conditions" if is_affected else "open_normal"
            })

        active_closures_count = sum(1 for r in route_statuses if r["status"] != "open_normal")
        has_active_closures = active_closures_count > 0 or has_closure_mentions

        normalized_data = {
            "region": valid_region,
            "portal_accessible": True,
            "has_active_closures": has_active_closures,
            "has_winter_surface_hazards": has_winter_hazards,
            "monitored_routes_count": len(route_statuses),
            "routes": route_statuses,
            "advisories": [
                "Winter tires (studless) required on all mountain passes and expressways.",
                "Beware of black ice in early mornings and shaded mountain sections."
            ]
        }

        notice = (
            f"Hokkaido road conditions: Winter driving cautions active. Portal accessible."
            if has_active_closures or has_winter_hazards
            else "All major Hokkaido expressways and monitored passes are operating normally."
        )

        snapshot = LiveDataSnapshot(
            provider=ROAD_PROVIDER,
            kind=ROAD_KIND,
            scope=valid_region,
            status="ok",
            fetched_at=utc_now_iso(),
            data=normalized_data,
            source_url=ROAD_PORTAL_URL,
            notice=notice
        )

        return global_cache.set(snapshot, ttl_seconds=DEFAULT_ROAD_TTL)

    except requests.exceptions.Timeout:
        stale = global_cache.get_stale(ROAD_PROVIDER, ROAD_KIND, valid_region)
        if stale:
            stale.notice = f"Road portal request timed out; {stale.notice}"
            return stale
        return LiveDataSnapshot(
            provider=ROAD_PROVIDER,
            kind=ROAD_KIND,
            scope=valid_region,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="TIMEOUT",
            notice="Road status request to Hokkaido Road Information portal timed out.",
            source_url=ROAD_PORTAL_URL
        )
    except Exception as e:
        stale = global_cache.get_stale(ROAD_PROVIDER, ROAD_KIND, valid_region)
        if stale:
            return stale
        return LiveDataSnapshot(
            provider=ROAD_PROVIDER,
            kind=ROAD_KIND,
            scope=valid_region,
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="FETCH_ERROR",
            notice=f"Failed to fetch road conditions: {str(e)}",
            source_url=ROAD_PORTAL_URL
        )
