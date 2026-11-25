"""Application configuration package.

Re-exports the Met Office API config (``config.metoffice``) and the UI
styling config (``config.ui``) so existing ``from config import X`` imports
keep working everywhere (client, weather_source, tests, demos).
"""

from config.metoffice import (
    MET_DAILY_URL,
    MET_HEADERS,
    MET_HOURLY_URL,
    MET_PARAMS,
    MET_REFRESH_MS,
    MET_THREE_HOURLY_URL,
    WEATHER_SWAP_MS,
)

__all__ = [
    "MET_DAILY_URL",
    "MET_HOURLY_URL",
    "MET_HEADERS",
    "MET_PARAMS",
    "MET_REFRESH_MS",
    "MET_THREE_HOURLY_URL",
    "WEATHER_SWAP_MS",
]