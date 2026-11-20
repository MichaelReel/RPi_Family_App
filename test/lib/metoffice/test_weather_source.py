"""Tests for CachedWeatherSource (lib/metoffice/weather_source.py)."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from lib.metoffice.models import DailyForecastPoint, HumanReadableWeatherReport
from lib.metoffice.weather_source import CachedWeatherSource


def _make_report() -> HumanReadableWeatherReport:
    day = DailyForecastPoint(
        date=datetime(2026, 11, 10),
        max_temperature_c=Decimal(18),
        min_temperature_c=Decimal(5),
        max_feels_like_c=Decimal(17),
        rain_probability_pct=20,
        snow_probability_pct=None,
        wind_speed_midday_mph=Decimal(10),
        wind_direction_midday_deg=90,
        visibility_midday_metres=8000,
        uv_index_max=3,
        weather_code=2,
        weather_condition="Partly cloudy",
    )
    return HumanReadableWeatherReport(
        location_name="Testville",
        coordinates=[Decimal("51.5"), Decimal("-0.1")],
        model_run_at=datetime(2026, 11, 9),
        forecast_days=[day],
        forecast_hourly=[],
        forecast_three_hourly=[],
    )


class TestCachedWeatherSource:
    @patch("lib.metoffice.weather_source.get_human_readable_weather")
    def test_first_call_fetches_and_caches(self, mock_fetch: MagicMock) -> None:
        """The first call should hit the API and cache the result."""
        mock_fetch.return_value = _make_report()
        source = CachedWeatherSource(ttl_ms=60_000)

        result = source.get_report()

        assert result is not None
        mock_fetch.assert_called_once()

    @patch("lib.metoffice.weather_source.get_human_readable_weather")
    def test_second_call_within_ttl_does_not_refetch(
        self, mock_fetch: MagicMock
    ) -> None:
        """Within the TTL window a second call returns the cache without re-fetching."""
        mock_fetch.return_value = _make_report()
        source = CachedWeatherSource(ttl_ms=60_000)

        first = source.get_report()
        second = source.get_report()

        assert first is second  # same object from cache
        assert mock_fetch.call_count == 1  # only one HTTP call

    @patch("lib.metoffice.weather_source.get_human_readable_weather")
    def test_stale_cache_refetches(self, mock_fetch: MagicMock) -> None:
        """After TTL expires the next call must re-fetch."""
        fresh = _make_report()
        stale = _make_report()
        mock_fetch.side_effect = [stale, fresh]
        source = CachedWeatherSource(ttl_ms=0)  # ttl=0 → immediately stale

        first = source.get_report()
        second = source.get_report()

        assert first is stale
        assert second is fresh
        assert mock_fetch.call_count == 2

    @patch("lib.metoffice.weather_source.get_human_readable_weather")
    def test_fetch_failure_returns_stale_cache(self, mock_fetch: MagicMock) -> None:
        """If the fetch fails but we have a cached report, serve the stale one."""
        cached = _make_report()
        source = CachedWeatherSource(ttl_ms=60_000)
        source._report = cached  # pre-populate cache
        source._fetched_at = None  # mark as stale

        mock_fetch.return_value = None  # simulate network failure
        result = source.get_report()

        assert result is cached  # fell back to stale cache

    @patch("lib.metoffice.weather_source.get_human_readable_weather")
    def test_fetch_failure_no_cache_returns_none(self, mock_fetch: MagicMock) -> None:
        """If the fetch fails and there is no cache, return None."""
        mock_fetch.return_value = None
        source = CachedWeatherSource(ttl_ms=60_000)

        result = source.get_report()

        assert result is None

    @patch("lib.metoffice.weather_source.get_human_readable_weather")
    def test_clear_cache_forces_refetch(self, mock_fetch: MagicMock) -> None:
        """clear_cache() should invalidate the cache so the next call refetches."""
        report = _make_report()
        mock_fetch.return_value = report
        source = CachedWeatherSource(ttl_ms=60_000)

        source.get_report()  # populate cache
        source.clear_cache()  # invalidate
        source.get_report()  # should refetch

        assert mock_fetch.call_count == 2

    def test_ttl_defaults_to_met_refresh_ms(self) -> None:
        """ttl_ms should default to MET_REFRESH_MS when not specified."""
        from config import MET_REFRESH_MS

        source = CachedWeatherSource()
        assert source._ttl_ms == MET_REFRESH_MS
