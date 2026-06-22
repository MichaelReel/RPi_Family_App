import requests

from PyQt6.QtWidgets import QApplication

from config import MET_DAILY_URL, MET_HEADERS, MET_PARAMS
from lib.metoffice.adapter import MetOfficeAdapter
from lib.metoffice.domain.models import WeatherSchemaRoot
from lib.metoffice.domain.schemas import WeatherSchemaRootSchema
from lib.metoffice.models import HumanReadableWeatherReport
from lib.metoffice.widgets.eight_day_grid import EightDayGridWidget



def get_human_readable_weather() -> HumanReadableWeatherReport:
    # Fetch and parse data
    response = requests.get(MET_DAILY_URL, headers=MET_HEADERS, params=MET_PARAMS)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        # TODO: We can let the schema raise an error for now, but will need to handle properly

    raw_weather_obj: WeatherSchemaRoot = WeatherSchemaRootSchema().load(response.json())
    return MetOfficeAdapter.to_human_readable(raw_weather_obj)


def main() -> None:
    app: QApplication = QApplication([])
    widget_window: EightDayGridWidget = EightDayGridWidget(report_source=get_human_readable_weather)
    widget_window.setWindowTitle("8-Day Reflow Weather Grid Tracker")

    # Might replace these 2 lines with widget_window.showFullScreen()
    widget_window.resize(850, 450)
    widget_window.show()

    app.exec()


if __name__ == "__main__":
    main()
