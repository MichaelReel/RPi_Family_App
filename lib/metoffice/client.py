import requests

from config import MET_DAILY_URL, MET_HEADERS, MET_PARAMS

from lib.metoffice.adapter import MetOfficeAdapter
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema
from lib.metoffice.models import HumanReadableWeatherReport


def get_human_readable_weather() -> HumanReadableWeatherReport:
    # Fetch and parse data
    response = requests.get(MET_DAILY_URL, headers=MET_HEADERS, params=MET_PARAMS)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        # TODO: We can let the schema raise an error for now, but will need to handle properly

    raw_weather_obj: WeatherSchemaRoot = WeatherSchemaRootSchema().load(response.json())
    return MetOfficeAdapter.to_human_readable(raw_weather_obj)
    