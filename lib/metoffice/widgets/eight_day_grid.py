import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, 
                             QVBoxLayout, QLabel, QFrame)
from PyQt6.QtCore import Qt

from lib.metoffice.models import DailyForecastPoint, HumanReadableWeatherReport
from lib.metoffice.widgets.day_card import DayCardWidget


class EightDayGridWidget(QWidget):
    """Grid frame that builds child DayCardWidgets and dynamically reflows layouts."""
    def __init__(self, report: HumanReadableWeatherReport, parent=None) -> None:
        super().__init__(parent)
        self.cards: list[DayCardWidget] = []
        self.current_columns: int = 0 
        
        self.grid_layout: QGridLayout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.setLayout(self.grid_layout)
        
        # Only take up to the first 8 items provided in forecast pipeline
        data_point: DailyForecastPoint
        for data_point in report.forecast_days[:8]:
            card: DayCardWidget = DayCardWidget(data_point)
            self.cards.append(card)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        target_cols = 4 if self.width() >= self.height() else 2
        if target_cols != self.current_columns:
            self.current_columns = target_cols
            self.rearrange_grid(target_cols)

    def rearrange_grid(self, cols):
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            
        for index, card in enumerate(self.cards):
            row = index // cols
            col = index % cols
            self.grid_layout.addWidget(card, row, col)
