"""JR Hokkaido Train Status Adapter.

Connects to real-time train operational feeds (Yahoo Transit / ODPT API).
Returns status='ok' on success, 'stale' on cache fallback, or 'unavailable' on network failure.
No fabricated or mocked simulation data is used.
"""

from external_data.models import LiveDataSnapshot
from external_data.trains import fetch_live_train_status


def fetch_train_status(line_name: str = "All") -> LiveDataSnapshot:
    """Fetches real-time JR Hokkaido train operational status.
    
    Connects to live transit providers. If unavailable, returns status='unavailable'
    with explicit error details. Never fabricates fake delays or success.
    """
    return fetch_live_train_status(line_name)
