import os
from decimal import Decimal
from typing import Final

_METOFFICE_URL: Final[str] = "https://data.hub.api.metoffice.gov.uk/"

MET_DAILY_URL: Final[str] = _METOFFICE_URL + "sitespecific/v0/point/daily"
MET_HOURLY_URL: Final[str] = _METOFFICE_URL + "sitespecific/v0/point/hourly"
MET_THREE_HOURLY_URL: Final[str] = _METOFFICE_URL + "sitespecific/v0/point/three-hourly"
MET_HEADERS: Final[dict[str, str]] = {
    "apikey": os.environ.get("METOFFICE_API_KEY", ""),
    "accept": "application/json",
}
MET_PARAMS: Final[dict[str, Decimal]] = {
    "latitude": Decimal(os.environ.get("METOFFICE_LATITUDE", "54.3")),
    "longitude": Decimal(os.environ.get("METOFFICE_LONGITUDE", "-7.3")),
}
MET_REFRESH_MS: Final[int] = 60 * 60 * 1000
WEATHER_SWAP_MS: Final[int] = 5 * 60 * 1000
WEATHER_ICON_DIM: Final[int] = 48
