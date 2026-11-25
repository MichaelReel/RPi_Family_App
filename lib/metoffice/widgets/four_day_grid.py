from collections.abc import Callable
from logging import Logger, getLogger
from typing import Final

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from config import MET_REFRESH_MS
from config.ui import (
    DAY_GRID_SPACING,
    FEATURED_DAY_CARD_STYLE,
    SECONDARY_DAY_CARD_STYLE,
)
from lib.metoffice.models import HumanReadableWeatherReport
from lib.metoffice.widgets.day_card import DayCardWidget

_LOGGER: Final[Logger] = getLogger(__name__)


class FourDayGridWidget(QWidget):
    """Layout frame that features Day 1 as a large card, with Days 2-4 arranged natively in a row below it."""

    def __init__(
        self,
        report_source: Callable[[], HumanReadableWeatherReport | None],
        bg_color: str = "#000022",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.report_source: Callable[[], HumanReadableWeatherReport | None] = (
            report_source
        )
        self._report: HumanReadableWeatherReport | None = None
        self._bg_color: str = bg_color
        self._cards: list[DayCardWidget] = []

        self._build_layouts()
        self._initialise_cards()
        self._start_refresh_timer()

    def _build_layouts(self) -> None:
        """Creates the outer vertical and secondary-row layouts for the grid."""
        self._main_layout: QVBoxLayout = QVBoxLayout()
        self._main_layout.setSpacing(DAY_GRID_SPACING)
        self.setLayout(self._main_layout)

        self._secondary_layout: QHBoxLayout = QHBoxLayout()
        self._secondary_layout.setSpacing(DAY_GRID_SPACING)
        self._secondary_layout.setContentsMargins(0, 0, 0, 0)

    def _start_refresh_timer(self) -> None:
        """Starts the periodic timer that refreshes the grid data in place."""
        self._refresh_timer: QTimer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_cards)
        self._refresh_timer.start(MET_REFRESH_MS)

    def _initialise_cards(self) -> None:
        """Fetches the report, builds the four cards, and attaches them to layouts."""
        self._fetch_report_for_setup()
        self._create_cards()
        self._attach_cards_to_layouts()

    def _fetch_report_for_setup(self) -> None:
        """Fetches the report used to build the grid, failing if it is unavailable."""
        try:
            self._report = self.report_source()
        except Exception:
            _LOGGER.exception("Error calling report_source during _initialise_cards")
            self._report = None

        if self._report is None:
            raise RuntimeError(
                "Due to met office API issues, this widget cannot be built"
            )

    def _create_cards(self) -> None:
        """Creates one card per forecast day, featuring the first at the top."""
        assert self._report is not None
        for index, data_point in enumerate(self._report.forecast_days[1:5]):
            config = FEATURED_DAY_CARD_STYLE if index == 0 else SECONDARY_DAY_CARD_STYLE
            card: DayCardWidget = DayCardWidget(data_point, config=config)
            self._cards.append(card)

    def _attach_cards_to_layouts(self) -> None:
        """Adds the featured and secondary cards to their respective layouts."""
        feature_card: DayCardWidget = self._cards[0]
        # Stretch=2 makes the top card twice as tall as the bottom layout group
        self._main_layout.addWidget(feature_card, stretch=2)

        secondary_card: DayCardWidget
        for secondary_card in self._cards[1:]:
            self._secondary_layout.addWidget(secondary_card)

        self._main_layout.addLayout(self._secondary_layout, stretch=1)

    def _refresh_cards(self) -> None:
        try:
            report: HumanReadableWeatherReport | None = self.report_source()
        except Exception:
            _LOGGER.exception("Error calling report_source during _refresh_cards")
            return

        if not report:
            _LOGGER.error("Due to met office API issues, this widget cannot be updated")
            return

        self._report = report

        index: int
        card: DayCardWidget
        for index, card in enumerate(self._cards):
            report_index: int = index + 1
            if report_index < len(self._report.forecast_days):
                # Data updates seamlessly because card properties read from its internal saved config
                card.update_data(self._report.forecast_days[report_index])
