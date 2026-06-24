from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import sys

from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, 
                             QVBoxLayout, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer

from config import MET_REFRESH_MS
from lib.metoffice.models import DailyForecastPoint, HumanReadableWeatherReport
from lib.metoffice.widgets.day_card import DayCardWidget


class EightDayGridWidget(QWidget):
    """Grid frame that builds child DayCardWidgets and dynamically reflows layouts."""
    def __init__(
        self,
        report_source: Callable[[], HumanReadableWeatherReport],
        bg_color: str ="#000022",
        parent: QWidget | None=None
    ) -> None:
        super().__init__(parent)
        self.report_source: Callable[[], HumanReadableWeatherReport] = report_source
        self._bg_color: str = bg_color
        self.cards: list[DayCardWidget] = []
        self.current_columns: int = 0 
        
        self.grid_layout: QGridLayout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.setLayout(self.grid_layout)

        self.setup_grid_data()

        self.refresh_timer: QTimer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_grid_data)
        self.refresh_timer.start(MET_REFRESH_MS)
        
    def setup_grid_data(self) -> None:
        report: HumanReadableWeatherReport = self.report_source()

        # Only take up to the first 8 items provided in forecast pipeline
        data_point: DailyForecastPoint
        for data_point in report.forecast_days[:8]:
            card: DayCardWidget = DayCardWidget(data_point)
            card.setStyleSheet(f"background-color: {self._bg_color};")
            self.cards.append(card)
    
    def update_grid_data(self) -> None:
        report: HumanReadableWeatherReport = self.report_source()

        index: int
        card: DayCardWidget
        for index, card in enumerate(self.cards):
            card.update_data(report.forecast_days[index])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        target_cols = 4 if self.width() >= self.height() else 2
        if target_cols != self.current_columns:
            self.current_columns = target_cols
            self.rearrange_grid(target_cols)

    def rearrange_grid(self, cols):
        card: DayCardWidget
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            
        index: int
        for index, card in enumerate(self.cards):
            row = index // cols
            col = index % cols
            self.grid_layout.addWidget(card, row, col)
