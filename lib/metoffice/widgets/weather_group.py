"""Widget that groups the location label and four-day forecast grid together."""
from collections.abc import Callable
from decimal import Decimal

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from lib.metoffice.models import HumanReadableWeatherReport
from lib.metoffice.widgets.four_day_grid import FourDayGridWidget
from lib.metoffice.widgets.location_label import LocationLabelWidget


class WeatherGroupWidget(QWidget):
    """Container that groups the location label and four-day forecast grid into a single widget.

    The FourDayGridWidget is responsible for its own data refresh via its internal timer;
    this widget simply provides a clean grouping so the weather view can be treated as
    a single unit (e.g., for stacking or swapping).
    """

    def __init__(
        self,
        report_source: Callable[[], HumanReadableWeatherReport],
        location_name: str | None,
        coordinates: list[Decimal] | None = None,
        bg_color: str = "#000022",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        layout: QVBoxLayout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.setLayout(layout)

        self.location_widget: LocationLabelWidget = LocationLabelWidget(
            location_name=location_name,
            coordinates=coordinates,
        )

        self.grid_widget: FourDayGridWidget = FourDayGridWidget(
            report_source=report_source,
            bg_color=bg_color,
        )

        layout.addWidget(self.location_widget)
        layout.addWidget(self.grid_widget)
