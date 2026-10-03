import requests
from datetime import datetime, timezone
from external_data.models import LiveDataSnapshot

KNOWN_COORDS = {
    "chitose airport": (141.6750, 42.7849),
    "new chitose airport": (141.6750, 42.7849),
    "sapporo": (141.3544, 43.0618),
    "otaru": (140.9934, 43.1894),
    "hakodate": (140.7367, 41.7687),
    "niseko": (140.6875, 42.8048),
    "asahikawa": (142.3649, 43.7709),
    "furano": (142.3832, 43.3421)
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_osrm_route_estimate(origin: str, destination: str, mode: str = "vehicle") -> LiveDataSnapshot:
    origin_key = origin.lower()
    dest_key = destination.lower()

    orig_c = KNOWN_COORDS.get(origin_key)
    dest_c = KNOWN_COORDS.get(dest_key)

    if not orig_c or not dest_c:
        return LiveDataSnapshot(
            provider="OSRM",
            kind="route_estimate",
            scope={"origin": origin, "destination": destination},
            status="error",
            fetched_at=_utc_now_iso(),
            expires_at=_utc_now_iso(),
            data={"error": "Coordinates not found."}
        )

    profile = "driving"
    if mode == "walk":
        profile = "walking"

    url = f"http://router.project-osrm.org/route/v1/{profile}/{orig_c[0]},{orig_c[1]};{dest_c[0]},{dest_c[1]}?overview=false"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            dist_km = route["distance"] / 1000.0
            duration_mins = route["duration"] / 60.0

            total_mins = int(duration_mins)
            if total_mins >= 60:
                h = total_mins // 60
                m = total_mins % 60
                time_str = f"{h} h, {m} min"
            else:
                time_str = f"{total_mins} min"

            disclaimer = ""
            actual_mode = mode
            if mode == "train" or mode == "bus":
                actual_mode = "car"
                disclaimer = f" Please explicitly warn the user that because real-time {mode} schedules are unavailable, you are providing the estimated time by car instead."

            summary = f" The estimated distance is {dist_km:.1f} km, which takes about {time_str} by {actual_mode}. Tell this to the user.{disclaimer}"

            return LiveDataSnapshot(
                provider="OSRM",
                kind="route_estimate",
                scope={"origin": origin, "destination": destination},
                status="ok",
                fetched_at=_utc_now_iso(),
                expires_at=_utc_now_iso(),
                data={
                    "distance_km": round(dist_km, 1),
                    "duration_mins": int(duration_mins),
                    "summary": summary
                }
            )
        else:
            raise ValueError("No route found from OSRM")

    except Exception as e:
        return LiveDataSnapshot(
            provider="OSRM",
            kind="route_estimate",
            scope={"origin": origin, "destination": destination},
            status="error",
            fetched_at=_utc_now_iso(),
            expires_at=_utc_now_iso(),
            data={"error": str(e)}
        )
