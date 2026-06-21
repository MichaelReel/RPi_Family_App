import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import pytest
from typing import Any

from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema
from lib.metoffice.adapter import MetOfficeAdapter
from lib.metoffice.models import HumanReadableWeatherReport, DailyForecastPoint

from test.test_data.metoffice_sitespecific_point_daily.model import expected_human_report_snapshot

@pytest.fixture
def sample_weather_root() -> WeatherSchemaRoot:
    """Fixture that loads the sample JSON file and deserialises it using the schema."""
    # Find the sample.json file relative to where this test file sits
    file_path = Path("test/test_data/metoffice_sitespecific_point_daily/domain.json").resolve()
       
    with open(file_path, "r", encoding="utf-8") as file:
        json_data: Any = json.load(file)
        
    # Deserialise into the raw strongly typed schema root object
    schema: WeatherSchemaRootSchema = WeatherSchemaRootSchema()
    return schema.load(json_data)


def test_adapter_transforms_metadata_correctly(sample_weather_root: WeatherSchemaRoot) -> None:
    """Verifies that the adapter cleanly parses global top-level metadata properties."""
    # Act
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(sample_weather_root)
    
    # Assert
    assert isinstance(report, HumanReadableWeatherReport)
    assert report.location_name is None
    assert isinstance(report.model_run_at, datetime)
    assert isinstance(report.coordinates, list)
    
    # Ensure coordinates parsed correctly as Decimal values
    for coord in report.coordinates:
        assert isinstance(coord, Decimal)


def test_adapter_transforms_timeseries_points(sample_weather_root: WeatherSchemaRoot) -> None:
    """Verifies the core timeline transformation loop maps attributes and data types."""
    # Act
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(sample_weather_root)
    
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
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(sample_weather_root)
    first_day: DailyForecastPoint = report.forecast_days[0]
    
    # Assert
    if first_day.visibility_midday_metres is not None:
        assert isinstance(first_day.visibility_midday_metres, int)
        # Real-world check: Met Office metrics shouldn't be 2-character strings like 'VG' or 'GO'
        assert first_day.visibility_midday_metres >= 0

def test_adapted_output_matches_fixture_snapshot(
    sample_weather_root: WeatherSchemaRoot, 
    expected_human_report_snapshot: HumanReadableWeatherReport
) -> None:
    """Performs a direct comparison between the adapted output and the known good snapshot fixture."""
    # Act: Run the adapter on the raw payload
    actual_report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(sample_weather_root)
    
    # Assert 1: Compare Top Level Metadata
    assert actual_report.location_name == expected_human_report_snapshot.location_name
    assert actual_report.coordinates == expected_human_report_snapshot.coordinates
    assert actual_report.model_run_at == expected_human_report_snapshot.model_run_at
    
    # Assert 2: Compare the Timeline Days Length
    # If comparing a partial timeline, you can slice it: actual_report.forecast_days[:1]
    assert len(actual_report.forecast_days) >= len(expected_human_report_snapshot.forecast_days)
    
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
        assert actual_day.wind_direction_midday_deg == expected_day.wind_direction_midday_deg
        assert actual_day.visibility_midday_metres == expected_day.visibility_midday_metres
        assert actual_day.uv_index_max == expected_day.uv_index_max