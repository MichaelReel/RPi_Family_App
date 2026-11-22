from PyQt6.QtWidgets import QApplication

from lib.metoffice.client import get_human_readable_weather
from lib.metoffice.widgets.four_day_grid import FourDayGridWidget


def main() -> None:
    app: QApplication = QApplication([])
    grid_widget: FourDayGridWidget = FourDayGridWidget(
        report_source=get_human_readable_weather
    )
    grid_widget.setWindowTitle("4-Day Weather Grid (demo)")

    grid_widget.resize(850, 450)
    grid_widget.show()

    app.exec()


if __name__ == "__main__":
    main()
