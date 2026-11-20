"""Caching weather data source that avoids duplicate HTTP calls.

`CachedWeatherSource` wraps the low-level `get_human_readable_weather()` call
with a TTL cache.  Multiple widgets can share a single instance so the
Met Office API is only hit once per refresh interval.
"""

import time
from logging import Logger, getLogger
from typing import Final

from config import MET_REFRESH_MS
from lib.metoffice.client import get_human_readable_weather
from lib.metoffice.models import HumanReadableWeatherReport

_LOGGER: Final[Logger] = getLogger(__name__)


class CachedWeatherSource:
    """TTL-cached wrapper around the Met Office weather fetch.

    Call `get_report()` to obtain the latest `HumanReadableWeatherReport`.
    The underlying HTTP call is only made when the cache is empty or older
    than `ttl_ms` milliseconds (defaults to `MET_REFRESH_MS`).

    Usage in `main.py::

        source = CachedWeatherSource()
        weather_group  = WeatherGroupWidget(report_source=source.get_report, ...)
        weather_graph  = WeatherGraphWidget(report_source=source.get_report, ...)
    """

    def __init__(self, ttl_ms: int = MET_REFRESH_MS) -> None:
        self._ttl_ms: int = ttl_ms
        self._report: HumanReadableWeatherReport | None = None
        self._fetched_at: float | None = (
            None  # time.monotonic() of last successful fetch
        )

    def get_report(self) -> HumanReadableWeatherReport | None:
        """Return a cached report, or fetch a fresh one if the cache is stale.

        Returns `None` when the fetch fails and no cached report is available.
        """
        if self._report is not None and self._is_fresh():
            return self._report

        fetched = get_human_readable_weather()
        if fetched is not None:
            self._report = fetched
            self._fetched_at = time.monotonic()
            return fetched

        # Fetch failed — fall back to stale cache if we have one
        if self._report is not None:
            _LOGGER.warning("Weather fetch failed; serving stale cached report")
            return self._report

        _LOGGER.error("Weather fetch failed and no cached report available")
        return None

    def clear_cache(self) -> None:
        """Invalidate the cache (e.g. for testing or manual refresh)."""
        self._report = None
        self._fetched_at = None

    def _is_fresh(self) -> bool:
        if self._fetched_at is None:
            return False
        elapsed_ms = (time.monotonic() - self._fetched_at) * 1000.0
        return elapsed_ms < self._ttl_ms
