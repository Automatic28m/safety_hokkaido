import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, Union
import json
from copy import deepcopy
from external_data.models import LiveDataSnapshot


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_to_utc(iso_str: str) -> Optional[datetime]:
    try:
        clean_str = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


class CacheStore:
    def __init__(self):
        self._store: Dict[Tuple[str, str, str], LiveDataSnapshot] = {}
        self._lock = threading.Lock()

    def _make_key(self, provider: str, kind: str, scope: Union[str, Dict[str, Any]]) -> Tuple[str, str, str]:
        if isinstance(scope, dict):
            scope_str = json.dumps(scope, sort_keys=True)
        else:
            scope_str = str(scope)
        return (provider.strip().lower(), kind.strip().lower(), scope_str.strip().lower())

    def get(self, provider: str, kind: str, scope: str) -> Optional[LiveDataSnapshot]:
        key = self._make_key(provider, kind, scope)
        with self._lock:
            snapshot = self._store.get(key)
            if not snapshot:
                return None

            if not snapshot.expires_at:
                return deepcopy(snapshot)

            expiry = parse_iso_to_utc(snapshot.expires_at)
            now = datetime.now(timezone.utc)
            if expiry and now <= expiry:
                return deepcopy(snapshot)

            return None

    def get_stale(self, provider: str, kind: str, scope: str) -> Optional[LiveDataSnapshot]:
        key = self._make_key(provider, kind, scope)
        with self._lock:
            snapshot = self._store.get(key)
            if not snapshot:
                return None

            stale_copy = deepcopy(snapshot)
            stale_copy.status = "stale"
            notice_prefix = "Serving stale cached data."
            if stale_copy.notice:
                stale_copy.notice = f"{notice_prefix} {stale_copy.notice}"
            else:
                stale_copy.notice = notice_prefix
            return stale_copy

    def set(self, snapshot: LiveDataSnapshot, ttl_seconds: int) -> LiveDataSnapshot:
        key = self._make_key(snapshot.provider, snapshot.kind, snapshot.scope)
        with self._lock:
            if not snapshot.expires_at and ttl_seconds > 0:
                fetched_dt = parse_iso_to_utc(snapshot.fetched_at)
                if not fetched_dt:
                    fetched_dt = datetime.now(timezone.utc)
                expiry_dt = fetched_dt + timedelta(seconds=ttl_seconds)
                snapshot.expires_at = expiry_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            self._store[key] = deepcopy(snapshot)
            return snapshot

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


global_cache = CacheStore()
