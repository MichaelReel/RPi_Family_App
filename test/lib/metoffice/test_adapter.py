import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest

from lib.metoffice.adapter import MetOfficeAdapter
from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema
from lib.metoffice.models import (
    DailyForecastPoint,
    HumanReadableWeatherReport,
    ThreeHourlyForecastPoint,
)


@pytest.fixture
def sample_weather_root() -> WeatherSchemaRoot:
    """Fixture that loads the sample JSON file and deserialises it using the schema."""
    # Find the sample.json file relative to where this test file sits
    file_path = Path(
        "test/test_data/metoffice_sitespecific_point_daily/domain.json"
    ).resolve()

    with open(file_path, encoding="utf-8") as file:
        json_data: Any = json.load(file)

    # Deserialise into the raw strongly typed schema root object
    schema: WeatherSchemaRootSchema = WeatherSchemaRootSchema()
    return cast(WeatherSchemaRoot, schema.load(json_data))


def test_adapter_transforms_metadata_correctly(
    sample_weather_root: WeatherSchemaRoot,
) -> None:
    """Verifies that the adapter cleanly parses global top-level metadata properties."""
    # Act
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(
        sample_weather_root, None
    )

    # Assert
    assert isinstance(report, HumanReadableWeatherReport)
    assert report.location_name is None
    assert isinstance(report.model_run_at, datetime)
    assert isinstance(report.coordinates, list)

    # Ensure coordinates parsed correctly as Decimal values
    for coord in report.coordinates:
        assert isinstance(coord, Decimal)


def test_adapter_transforms_timeseries_points(
    sample_weather_root: WeatherSchemaRoot,
) -> None:
    """Verifies the core timeline transformation loop maps attributes and data types."""
    # Act
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(
        sample_weather_root, None
    )

    # Assert
    assert len(report.forecast_days) > 0

    # Inspect the very first parsed timeline point
    first_day: DailyForecastPoint = report.forecast_days[0]

    assert isinstance(first_day, DailyForecastPoint)
    assert isinstance(first_day.date, datetime)
    assert isinstance(first_day.weather_condition, str)

    # The string shouldn't look like raw data fallback numbers (e.g. "Unknown Code (7)")
    assert "Code (" not in first_day.weather_condition

    # Verify our custom type rules (Decimal vs Optional typing)
    if first_day.max_temperature_c is not None:
        assert isinstance(first_day.max_temperature_c, Decimal)

    if first_day.rain_probability_pct is not None:
        assert isinstance(first_day.rain_probability_pct, int)
        assert 0 <= first_day.rain_probability_pct <= 100


def test_visibility_parsed_as_metres(sample_weather_root: WeatherSchemaRoot) -> None:
    """Ensures that midday or midnight visibility handles native integers instead of old text codes."""
    # Act
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(
        sample_weather_root, None
    )
    first_day: DailyForecastPoint = report.forecast_days[0]

    # Assert
    if first_day.visibility_midday_metres is not None:
        assert isinstance(first_day.visibility_midday_metres, int)
        # Real-world check: Met Office metrics shouldn't be 2-character strings like 'VG' or 'GO'
        assert first_day.visibility_midday_metres >= 0


def test_adapted_output_matches_fixture_snapshot(
    sample_weather_root: WeatherSchemaRoot,
    expected_human_report_snapshot: HumanReadableWeatherReport,
) -> None:
    """Performs a direct comparison between the adapted output and the known good snapshot fixture."""
    # Act: Run the adapter on the raw payload
    actual_report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(
        sample_weather_root, None
    )

    # Assert 1: Compare Top Level Metadata
    assert actual_report.location_name == expected_human_report_snapshot.location_name
    assert actual_report.coordinates == expected_human_report_snapshot.coordinates
    assert actual_report.model_run_at == expected_human_report_snapshot.model_run_at

    # Assert 2: Compare the Timeline Days Length
    # If comparing a partial timeline, you can slice it: actual_report.forecast_days[:1]
    assert len(actual_report.forecast_days) >= len(
        expected_human_report_snapshot.forecast_days
    )

    # Assert 3: Deep compare individual fields on the first day
    i: int
    expected_day: DailyForecastPoint
    for i, expected_day in enumerate(expected_human_report_snapshot.forecast_days):
        actual_day: DailyForecastPoint = actual_report.forecast_days[i]

        assert actual_day == expected_day

        assert actual_day.date == expected_day.date
        assert actual_day.weather_condition == expected_day.weather_condition
        assert actual_day.max_temperature_c == expected_day.max_temperature_c
        assert actual_day.min_temperature_c == expected_day.min_temperature_c
        assert actual_day.max_feels_like_c == expected_day.max_feels_like_c
        assert actual_day.rain_probability_pct == expected_day.rain_probability_pct
        assert actual_day.snow_probability_pct == expected_day.snow_probability_pct
        assert actual_day.wind_speed_midday_mph == expected_day.wind_speed_midday_mph
        assert (
            actual_day.wind_direction_midday_deg
            == expected_day.wind_direction_midday_deg
        )
        assert (
            actual_day.visibility_midday_metres == expected_day.visibility_midday_metres
        )
        assert actual_day.uv_index_max == expected_day.uv_index_max


def test_missing_weather_code_defaults_to_unknown(
    sample_weather_root: WeatherSchemaRoot,
) -> None:
    """When both day and night weather codes are missing, the adapter should produce None and 'Unknown'."""
    # Mutate the first timeSeries entry to strip both weather code keys
    first_entry = sample_weather_root.features[0].properties.time_series[0]
    first_entry.data.pop("daySignificantWeatherCode", None)
    first_entry.data.pop("nightSignificantWeatherCode", None)

    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(
        sample_weather_root, None
    )
    first_day: DailyForecastPoint = report.forecast_days[0]

    assert first_day.weather_code is None
    assert first_day.weather_condition == "Unknown"


@pytest.fixture
def sample_three_hourly_root() -> WeatherSchemaRoot:
    """Load the 3-hourly sample JSON and deserialise it using the schema."""
    file_path = Path(
        "test/test_data/metoffice_sitespecific_point_threehourly/domain.json"
    ).resolve()
    with open(file_path, encoding="utf-8") as file:
        json_data: Any = json.load(file)
    schema: WeatherSchemaRootSchema = WeatherSchemaRootSchema()
    return cast(WeatherSchemaRoot, schema.load(json_data))


def test_adapter_parses_three_hourly_points(
    sample_three_hourly_root: WeatherSchemaRoot,
) -> None:
    """The adapter should map 3-hourly keys (incl. feelsLikeTemp/min|maxScreenAirTemp)."""
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(
        None, None, sample_three_hourly_root
    )

    assert len(report.forecast_three_hourly) == 4

    first = report.forecast_three_hourly[0]
    assert isinstance(first, ThreeHourlyForecastPoint)
    assert isinstance(first.time, datetime)
    assert first.time.year == 2026 and first.time.month == 11 and first.time.day == 15

    # 3-hourly specific fields
    assert first.min_screen_temperature_c == Decimal("6.1")
    assert first.max_screen_temperature_c == Decimal("11.4")
    # feelsLikeTemp (3-hourly key, not feelsLikeTemperature) maps to feels_like
    assert first.feels_like_temperature_c == Decimal("5.9")
    assert first.screen_temperature_c == Decimal("8.2")

    # Shared fields
    assert first.wind_speed_10m_mph == Decimal("6.5")
    assert first.wind_gust_10m_mph == Decimal("12.0")
    assert first.wind_direction_10m_deg == 220
    assert first.prob_of_precipitation_pct == 70
    assert first.uv_index == 0
    assert first.significant_weather_code == 10


def test_adapter_three_hourly_defaults_empty_when_none() -> None:
    """When no 3-hourly root is supplied the report should carry an empty list."""
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(None, None)
    assert report.forecast_three_hourly == []


def test_hourly_parser_captures_min_max_screen_temp() -> None:
    """Hourly points must expose minScreenAirTemp/maxScreenAirTemp.

    Regression for the flat min/max line: the 1-hourly API returns per-point
    min/max temps, and the adapter must map them so the temp-lane min/max
    lines can be continuous over the first 48h (hourly span).
    """
    hourly_payload = {
        "type": "FeatureCollection",
        "parameters": [],
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-7.3, 54.3, 0]},
                "properties": {
                    "requestPointDistance": 0.0,
                    "modelRunDate": "2026-11-15T16:00Z",
                    "timeSeries": [
                        {
                            "time": "2026-11-15T16:00Z",
                            "screenTemperature": 8.4,
                            "minScreenAirTemp": 6.2,
                            "maxScreenAirTemp": 10.1,
                            "feelsLikeTemperature": 6.0,
                            "windSpeed10m": 7.0,
                            "windGustSpeed10m": 14.0,
                            "windDirectionFrom10m": 200,
                            "screenRelativeHumidity": 88.0,
                            "precipitationRate": 0.1,
                            "totalPrecipAmount": 0.5,
                            "probOfPrecipitation": 40,
                            "uvIndex": 1,
                            "significantWeatherCode": 3,
                        }
                    ],
                },
            }
        ],
    }
    root: WeatherSchemaRoot = WeatherSchemaRootSchema().load(hourly_payload)
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(
        None, root, None
    )

    assert len(report.forecast_hourly) == 1
    point = report.forecast_hourly[0]
    assert point.min_screen_temperature_c == Decimal("6.2")
    assert point.max_screen_temperature_c == Decimal("10.1")
    assert point.screen_temperature_c == Decimal("8.4")
