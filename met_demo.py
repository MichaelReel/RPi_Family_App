import requests

from PyQt6.QtWidgets import QApplication

from lib.metoffice.client import get_human_readable_weather
from lib.metoffice.widgets.eight_day_grid import FourDayGridWidget


def main() -> None:
    app: QApplication = QApplication([])
    widget_window: FourDayGridWidget = FourDayGridWidget(report_source=get_human_readable_weather)
    widget_window.setWindowTitle("8-Day Reflow Weather Grid Tracker")

    # Might replace these 2 lines with widget_window.showFullScreen()
    widget_window.resize(850, 450)
    widget_window.show()

    app.exec()


if __name__ == "__main__":
    main()
