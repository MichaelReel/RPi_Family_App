from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class HourlyForecastPoint:
    time: datetime
    screen_temperature_c: Decimal | None
    min_screen_temperature_c: Decimal | None
    max_screen_temperature_c: Decimal | None
    feels_like_temperature_c: Decimal | None
    wind_speed_10m_mph: Decimal | None
    wind_gust_10m_mph: Decimal | None
    wind_direction_10m_deg: int | None
    relative_humidity_pct: Decimal | None
    precipitation_rate_mmh: Decimal | None
    total_precip_amount_mm: Decimal | None
    prob_of_precipitation_pct: int | None
    uv_index: int | None
    significant_weather_code: int | None


@dataclass
class ThreeHourlyForecastPoint:
    time: datetime
    screen_temperature_c: Decimal | None
    min_screen_temperature_c: Decimal | None
    max_screen_temperature_c: Decimal | None
    feels_like_temperature_c: Decimal | None
    wind_speed_10m_mph: Decimal | None
    wind_gust_10m_mph: Decimal | None
    wind_direction_10m_deg: int | None
    relative_humidity_pct: Decimal | None
    precipitation_rate_mmh: Decimal | None
    total_precip_amount_mm: Decimal | None
    prob_of_precipitation_pct: int | None
    uv_index: int | None
    significant_weather_code: int | None


@dataclass
class DailyForecastPoint:
    date: datetime
    max_temperature_c: Decimal | None
    min_temperature_c: Decimal | None
    max_feels_like_c: Decimal | None
    rain_probability_pct: int | None
    snow_probability_pct: int | None
    wind_speed_midday_mph: Decimal | None
    wind_direction_midday_deg: int | None
    visibility_midday_metres: int | None
    uv_index_max: int | None
    weather_code: int | None
    weather_condition: str


@dataclass
class HumanReadableWeatherReport:
    location_name: str | None
    coordinates: list[Decimal]
    model_run_at: datetime
    forecast_days: list[DailyForecastPoint]
    forecast_hourly: list[HourlyForecastPoint]
    forecast_three_hourly: list[ThreeHourlyForecastPoint]
