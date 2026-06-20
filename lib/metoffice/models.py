from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


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
    weather_condition: str

@dataclass
class HumanReadableWeatherReport:
    location_name: str | None
    coordinates: list[Decimal]
    model_run_at: datetime
    forecast_days: list[DailyForecastPoint]
