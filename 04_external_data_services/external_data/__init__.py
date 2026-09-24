"""Adapters for live weather, disaster, and transport data."""

from external_data.models import LiveDataSnapshot
from external_data.cache import CacheStore, global_cache
from external_data.weather import fetch_real_time_weather
from external_data.disaster import fetch_disaster_warnings
from external_data.train import fetch_train_status
from external_data.tools import (
    get_real_time_weather,
    get_disaster_warnings,
    check_train_status,
    WEATHER_TOOL_SCHEMA,
    DISASTER_TOOL_SCHEMA,
    TRAIN_TOOL_SCHEMA,
)

__all__ = [
    "LiveDataSnapshot",
    "CacheStore",
    "global_cache",
    "fetch_real_time_weather",
    "fetch_disaster_warnings",
    "fetch_train_status",
    "get_real_time_weather",
    "get_disaster_warnings",
    "check_train_status",
    "WEATHER_TOOL_SCHEMA",
    "DISASTER_TOOL_SCHEMA",
    "TRAIN_TOOL_SCHEMA",
]
