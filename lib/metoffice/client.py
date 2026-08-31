from http import HTTPStatus

import requests
from urllib3.exceptions import HTTPError

from config import MET_DAILY_URL, MET_HEADERS, MET_PARAMS
from lib.metoffice.adapter import MetOfficeAdapter
from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema
from lib.metoffice.models import HumanReadableWeatherReport


def get_human_readable_weather() -> HumanReadableWeatherReport | None:
    # Fetch and parse data
    try:
        response = requests.get(MET_DAILY_URL, headers=MET_HEADERS, params=MET_PARAMS)
    except HTTPError as http_error:
        print(f"Exception {http_error} occurred getting weather info")
        return None

    if response.status_code != HTTPStatus.OK:
        print(f"Error {response.status_code}: {response.text}")
        return None

    raw_weather_obj: WeatherSchemaRoot = WeatherSchemaRootSchema().load(response.json())
    return MetOfficeAdapter.to_human_readable(raw_weather_obj)
