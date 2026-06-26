from collections.abc import Callable
from typing import Final

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import QTimer

from config import MET_REFRESH_MS
from lib.metoffice.models import HumanReadableWeatherReport, DailyForecastPoint
from lib.metoffice.widgets.day_card import DayCardWidget


class FourDayGridWidget(QWidget):
    """Layout frame that features Day 1 as a large card, with Days 2-4 arranged natively in a row below it."""
    
    def __init__(
        self,
        report_source: Callable[[], HumanReadableWeatherReport],
        bg_color: str = "#000022",
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.report_source: Callable[[], HumanReadableWeatherReport] = report_source
        self._bg_color: str = bg_color
        self.cards: list[DayCardWidget] = []
        
        # Core outer vertical container layout
        self.main_layout: QVBoxLayout = QVBoxLayout()
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

        # Bottom row layout for the 3 secondary weather cards
        self.secondary_layout: QHBoxLayout = QHBoxLayout()
        self.secondary_layout.setSpacing(10)
        self.secondary_layout.setContentsMargins(0, 0, 0, 0)

        self.setup_grid_data()
        
        self.refresh_timer: QTimer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_grid_data)
        self.refresh_timer.start(MET_REFRESH_MS)
        
    def setup_grid_data(self) -> None:
        report: HumanReadableWeatherReport = self.report_source()

        # Extract exactly 4 items (Indices 1 to 4)
        data_point: DailyForecastPoint
        for data_point in report.forecast_days[1:5]:
            card: DayCardWidget = DayCardWidget(data_point)
            card.setStyleSheet(f"background-color: {self._bg_color};")
            self.cards.append(card)

        # Feature Card (Index 1 from the forecast pipeline, first item in self.cards)
        feature_card: DayCardWidget = self.cards[0]
        # Stretch=2 makes the top card twice as tall as the bottom layout group
        self.main_layout.addWidget(feature_card, stretch=2)
        
        # Populate the remaining 3 cards into the bottom row layout
        secondary_card: DayCardWidget
        for secondary_card in self.cards[1:]:
            self.secondary_layout.addWidget(secondary_card)
            
        # Add the bottom row layout directly to the main layout tree
        self.main_layout.addLayout(self.secondary_layout, stretch=1)
    
    def update_grid_data(self) -> None:
        report: HumanReadableWeatherReport = self.report_source()

        index: int
        card: DayCardWidget
        for index, card in enumerate(self.cards):
            report_index: int = index + 1
            if report_index < len(report.forecast_days):
                card.update_data(report.forecast_days[report_index])
                card.setStyleSheet(f"background-color: {self._bg_color};")
