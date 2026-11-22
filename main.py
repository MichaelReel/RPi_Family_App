from PyQt6.QtWidgets import QApplication, QBoxLayout, QMainWindow, QPushButton, QWidget

from config import WEATHER_SWAP_MS
from lib.clock.widgets.live_clock import LiveClockWidget
from lib.metoffice.weather_source import CachedWeatherSource
from lib.metoffice.widgets.weather_graph import WeatherGraphWidget
from lib.metoffice.widgets.weather_group import WeatherGroupWidget
from lib.widgets.swapping_container import SwappingContainerWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Custom Full Screen App")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self._main_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom, central_widget)
        self._main_layout.setSpacing(10)
        self._main_layout.setContentsMargins(10, 10, 10, 10)

        bg_color: str = "#000022"
        text_color: str = "#0000aa"
        hour_minutes_color: str = "#0000FF"
        seconds_color: str = "#000088"
        day_color: str = "#0000FF"
        date_color: str = "#0000FF"

        self.setStyleSheet(f"background-color: {bg_color};color: {text_color};")

        self._clock_widget: LiveClockWidget = self._build_clock_section(
            hour_minutes_color=hour_minutes_color,
            seconds_color=seconds_color,
            day_color=day_color,
            date_color=date_color,
        )
        self._weather_container: SwappingContainerWidget = self._build_weather_section(
            bg_color=bg_color
        )

        self._main_layout.addWidget(self._clock_widget)
        self._main_layout.addWidget(self._weather_container)
        self._main_layout.addWidget(self._add_exit_button())

        self.showFullScreen()

    def _build_clock_section(
        self,
        hour_minutes_color: str,
        seconds_color: str,
        day_color: str,
        date_color: str,
    ) -> LiveClockWidget:
        """Build the live clock widget with the app's clock colours."""
        return LiveClockWidget(
            hour_minutes_color=hour_minutes_color,
            seconds_color=seconds_color,
            day_color=day_color,
            date_color=date_color,
            include_day=False,
            include_date=False,
        )

    def _build_weather_section(self, bg_color: str) -> SwappingContainerWidget:
        """Build the swapping weather container (group + graph pages)."""
        # Shared cached weather source — both widgets hit the API at most
        # once per MET_REFRESH_MS interval instead of each calling it independently.
        weather_source = CachedWeatherSource()

        # Fetch the report once at startup to extract the location name
        initial_report = weather_source.get_report()
        location_name = initial_report.location_name if initial_report else None
        coordinates = initial_report.coordinates if initial_report else None

        weather_group = WeatherGroupWidget(
            report_source=weather_source.get_report,
            location_name=location_name,
            coordinates=coordinates,
            bg_color=bg_color,
        )
        weather_graph = WeatherGraphWidget(
            report_source=weather_source.get_report,
            bg_color=bg_color,
        )
        return SwappingContainerWidget(
            pages=[weather_group, weather_graph],
            swap_interval_ms=WEATHER_SWAP_MS,
            bg_color=bg_color,
        )

    def _add_exit_button(self) -> QPushButton:
        """Build the exit button wired to close the window."""
        exit_button = QPushButton("Exit")
        exit_button.pressed.connect(self.close)
        return exit_button


def main() -> None:
    app = QApplication([])
    # Keep a strong reference so the window is not garbage-collected before
    # app.exec() runs (an unassigned top-level QWidget is destroyed immediately).
    window = MainWindow()  # noqa: F841  # reference must outlive app.exec()
    app.exec()


if __name__ == "__main__":
    main()
