from decimal import Decimal
import os
import requests
from typing import Final

from PyQt6.QtWidgets import QApplication

from lib.metoffice.adapter import MetOfficeAdapter
from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema
from lib.metoffice.models import HumanReadableWeatherReport
from lib.metoffice.widgets.eight_day_grid import EightDayGridWidget


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


def main():

    # Fetch and parse data
    response = requests.get(_DAILY_URL, headers=_HEADERS, params=_PARAMS)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        # TODO: We can let the schema raise an error for now, but will need to handle properly

    raw_weather_obj: WeatherSchemaRoot = WeatherSchemaRootSchema().load(response.json())
    report: HumanReadableWeatherReport = MetOfficeAdapter.to_human_readable(raw_weather_obj)

    app: QApplication = QApplication([])
    widget_window: EightDayGridWidget = EightDayGridWidget(report)
    widget_window.setWindowTitle("8-Day Reflow Weather Grid Tracker")

    # Might replace these 2 lines with widget_window.showFullScreen()
    widget_window.resize(850, 450)
    widget_window.show()

    app.exec()


if __name__ == "__main__":
    main()
