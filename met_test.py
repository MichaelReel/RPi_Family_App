from decimal import Decimal
import os
import requests
from typing import Final

from lib.metoffice.adapter import MetOfficeAdapter
from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema
from lib.metoffice.models import HumanReadableWeatherReport


_API_KEY: Final[str] = os.environ.get("METOFFICE_API_KEY")
_LATITUDE: Final[Decimal] = Decimal(os.environ.get("METOFFICE_LATITUDE", "54.3"))
_LONGITUDE: Final[Decimal] = Decimal(os.environ.get("METOFFICE_LONGITUDE", "-7.3"))

if not _API_KEY:
    raise ValueError("Unconfigured METOFFICE_API_KEY in environment")

_METOFFICE_URL: Final[str] = "https://data.hub.api.metoffice.gov.uk/"
_DAILY_URL: Final[str] = _METOFFICE_URL + "sitespecific/v0/point/daily"

_HEADERS: Final[dict[str, str]] = {
    "apikey": _API_KEY,
    "accept": "application/json"
}

_PARAMS: Final[dict[str, str]] = {
    "latitude": str(_LATITUDE),
    "longitude": str(_LONGITUDE)
}

# Fetch and parse data
response = requests.get(_DAILY_URL, headers=_HEADERS, params=_PARAMS)

if response.status_code == 200:

    raw_weather_obj: WeatherSchemaRoot = WeatherSchemaRootSchema().load(response.json())
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(raw_weather_obj)

    location: str = report.location_name if report.location_name else str(report.coordinates)

    print(f"Weather Report For: {location}")
    print(f"Data generated at: {report.model_run_at:%Y-%m-%d %H:%M}")

    for day in report.forecast_days:
        print(f"\nDate: {day.date:%A, %b %d}")
        print(f"  Condition:       {day.weather_condition}")
        print(f"  Max Temp:        {day.max_temperature_c}°C")
        print(f"  Chance of Rain:  {day.rain_probability_pct}%")
        print(f"  Visibility:      {day.visibility_midday_metres}")

else:
    print(f"Error {response.status_code}: {response.text}")
