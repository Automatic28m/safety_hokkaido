from external_data.models import LiveDataSnapshot
from external_data.cache import global_cache, utc_now_iso
from external_data.validation import validate_line_name

TRAIN_PROVIDER = "jr_hokkaido_simulator"
TRAIN_KIND = "train"
DEFAULT_TRAIN_TTL = 300
OFFICIAL_JR_SOURCE = "https://www.jrhokkaido.co.jp/"


def fetch_train_status(line_name: str = "All") -> LiveDataSnapshot:
    is_valid, valid_line, err_msg = validate_line_name(line_name)
    if not is_valid:
        return LiveDataSnapshot(
            provider=TRAIN_PROVIDER,
            kind=TRAIN_KIND,
            scope=str(line_name),
            status="unavailable",
            fetched_at=utc_now_iso(),
            error_code="INVALID_INPUT",
            notice=err_msg,
            source_url=OFFICIAL_JR_SOURCE
        )

    cached = global_cache.get(TRAIN_PROVIDER, TRAIN_KIND, valid_line)
    if cached:
        return cached

    lower_line = valid_line.lower()
    is_airport = "airport" in lower_line

    normalized_data = {
        "line_name": valid_line,
        "is_simulated": True,
        "verification_status": "unverified_mock",
        "simulation_details": {
            "operational_state": "delayed" if is_airport else "normal",
            "estimated_delay_minutes": 20 if is_airport else 0,
            "cause": "track_snow_accumulation" if is_airport else None,
            "affected_section": "Sapporo - New Chitose Airport" if is_airport else "Full Route"
        }
    }

    notice = (
        "Simulated status. Official JR Hokkaido live scraping adapter is not yet verified "
        "or active; do not treat as official real-time data."
    )

    snapshot = LiveDataSnapshot(
        provider=TRAIN_PROVIDER,
        kind=TRAIN_KIND,
        scope=valid_line,
        status="mocked",
        fetched_at=utc_now_iso(),
        data=normalized_data,
        source_url=OFFICIAL_JR_SOURCE,
        notice=notice
    )

    return global_cache.set(snapshot, ttl_seconds=DEFAULT_TRAIN_TTL)
