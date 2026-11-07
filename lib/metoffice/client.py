from http import HTTPStatus
from logging import Logger, getLogger
from typing import Final

import requests
from requests.exceptions import RequestException

from config import MET_DAILY_URL, MET_HEADERS, MET_PARAMS
from lib.metoffice.adapter import MetOfficeAdapter
from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema
from lib.metoffice.models import HumanReadableWeatherReport

_LOGGER: Final[Logger] = getLogger(__name__)
HTTP_TIMEOUT: Final[int] = 30


def get_human_readable_weather() -> HumanReadableWeatherReport | None:
    # Fetch and parse data
    try:
        response = requests.get(MET_DAILY_URL, headers=MET_HEADERS, params=MET_PARAMS, timeout=HTTP_TIMEOUT)
    except RequestException as req_error:
        _LOGGER.error("Exception occurred getting weather info: %s", req_error)
        return None

    if response.status_code != HTTPStatus.OK:
        _LOGGER.error("HTTP %s: %s", response.status_code, response.text)
        return None

    try:
        raw_weather_obj: WeatherSchemaRoot = WeatherSchemaRootSchema().load(response.json())
    except requests.exceptions.JSONDecodeError as json_error:
        _LOGGER.error("Failed to parse JSON response: %s", json_error)
        return None

    return MetOfficeAdapter.to_human_readable(raw_weather_obj)
