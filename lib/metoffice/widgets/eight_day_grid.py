from collections.abc import Callable
from enum import Enum, auto
from typing import Final, Dict

from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QResizeEvent

from config import MET_REFRESH_MS
from lib.metoffice.models import HumanReadableWeatherReport, DailyForecastPoint
from lib.metoffice.widgets.day_card import DayCardWidget


class LayoutMode(Enum):
    """Layout states for the grid alignment."""
    HORIZONTAL = auto()
    VERTICAL = auto()
    SQUARE = auto()


# Dictionary mapping each LayoutMode to its respective column count
LAYOUT_COLUMN_MAP: Final[Dict[LayoutMode, int]] = {
    LayoutMode.HORIZONTAL: 4,  # 1x4 horizontal strip
    LayoutMode.VERTICAL: 1,    # 4x1 vertical column
    LayoutMode.SQUARE: 2,      # 2x2 grid block
}


class FourDayGridWidget(QWidget):
    """Grid frame that builds 4 DayCardWidgets and rearranges into Horizontal, Vertical, or Square layouts."""
    
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
        
        # Track the active layout style Enum (None initially to force first render)
        self.current_layout_mode: LayoutMode | None = None 
        
        self.grid_layout: QGridLayout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.setLayout(self.grid_layout)

        self.setup_grid_data()

        self.refresh_timer: QTimer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_grid_data)
        self.refresh_timer.start(MET_REFRESH_MS)
        
    def setup_grid_data(self) -> None:
        report: HumanReadableWeatherReport = self.report_source()

        # Slice indices 1 to 4 (extracts exactly 4 sub-widgets, skipping index 0)
        data_point: DailyForecastPoint
        for data_point in report.forecast_days[1:5]:
            card: DayCardWidget = DayCardWidget(data_point)
            card.setStyleSheet(f"background-color: {self._bg_color};")
            self.cards.append(card)
    
    def update_grid_data(self) -> None:
        report: HumanReadableWeatherReport = self.report_source()

        # Safely align with the sliced 1:5 indices during data updates
        index: int
        card: DayCardWidget
        for index, card in enumerate(self.cards):
            report_index: int = index + 1
            if report_index < len(report.forecast_days):
                card.update_data(report.forecast_days[report_index])
                card.setStyleSheet(f"background-color: {self._bg_color};")

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        width: int = self.width()
        height: int = self.height()
        
        # Guard against zero-division errors if widget is fully collapsed
        aspect_ratio: float = width / height if height > 0 else 1.0

        # Determine structural orientation from window aspect ratios using Enum
        target_mode: LayoutMode
        if aspect_ratio >= 2.0:
            target_mode = LayoutMode.HORIZONTAL
        elif aspect_ratio <= 0.5:
            target_mode = LayoutMode.VERTICAL
        else:
            target_mode = LayoutMode.SQUARE

        # Only rebuild structure if the layout layout state changes
        if target_mode != self.current_layout_mode:
            self.current_layout_mode = target_mode
            self.rearrange_grid(target_mode)

    def rearrange_grid(self, mode: LayoutMode) -> None:
        # Step 1: Safely decouple cards from the layout
        card: DayCardWidget
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            
        # Step 2: Fetch target column sizes using the lookup map
        cols: int = LAYOUT_COLUMN_MAP[mode]

        # Step 3: Re-inject elements back to grid positions
        index: int
        for index, card in enumerate(self.cards):
            row: int = index // cols
            col: int = index % cols
            self.grid_layout.addWidget(card, row, col)
