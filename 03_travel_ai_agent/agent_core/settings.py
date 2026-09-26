"""Single place where node 03 reads values from ``02_api_backend/config.py``.

The config module is optional (unit tests and standalone tools may run without
node 02 on the path), so every lookup falls back to an explicit default.
"""
from __future__ import annotations

from typing import Any

try:
    from config import config as _config
except Exception:  # pragma: no cover - node 02 config absent
    _config = None


def config_value(name: str, default: Any) -> Any:
    """Returns ``config.<name>`` when node 02's config is importable, else ``default``."""
    if _config is None:
        return default
    return getattr(_config, name, default)


def provider_ready(client: Any) -> bool:
    """True when a provider client exists and reports that it is configured."""
    return client is not None and bool(getattr(client, "is_configured", True))
