from collections.abc import Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from config import MET_REFRESH_MS
from lib.metoffice.models import HumanReadableWeatherReport
from lib.metoffice.widgets.day_card import (
    CardStyleConfig,
    DayCardWidget,
    UIElementStyle,
)


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
        self.report: HumanReadableWeatherReport | None = None
        self._bg_color: str = bg_color
        self.cards: list[DayCardWidget] = []
        
        # 1. Initialize custom design configurations using the new data structure
        self.feature_config: CardStyleConfig = CardStyleConfig(
            widget_stylesheet=f"DayCardWidget {{ background-color: {self._bg_color}; border: 0px solid #007bff; border-radius: 8px; }}",
            weather_icon_dim=400,
            metric_icon_dim=38,
            layout_spacing=12,
            row_spacing=10,
            date_style=UIElementStyle(font_size="18px", font_weight="bold", text_color="#ffffff"),
            condition_style=UIElementStyle(font_size="80px", font_weight="500", text_color="#cccccc"),
            metrics_style=UIElementStyle(font_size="38px", text_color="#999999")
        )
        
        self.secondary_config: CardStyleConfig = CardStyleConfig(
            widget_stylesheet=f"DayCardWidget {{ background-color: {self._bg_color}; border: 1px solid #cccccc; border-radius: 6px; }}",
            weather_icon_dim=100,
            metric_icon_dim=16,
            layout_spacing=6,
            row_spacing=8,
            date_style=UIElementStyle(font_size="14px", font_weight="bold", text_color="#0056b3"),
            condition_style=UIElementStyle(font_size="20px", font_weight="500", text_color="#cccccc"),
            metrics_style=UIElementStyle(font_size="13px", text_color="#888888")
        )
        
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
        self.report = self.report_source()

        if self.report is None:
            raise RuntimeError("Due to met office API issues, this widget cannot be built")

        # Extract exactly 4 items (Indices 1 to 4)
        for i, data_point in enumerate(self.report.forecast_days[1:5]):
            # Assign the large profile to the first index, and standard profiles to the rest
            config = self.feature_config if i == 0 else self.secondary_config
            
            card: DayCardWidget = DayCardWidget(data_point, config=config)
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
        report: HumanReadableWeatherReport | None = self.report_source()

        if not report:
            print("Due to met office API issues, this widget cannot be updated")
            return
        
        self.report = report

        index: int
        card: DayCardWidget
        for index, card in enumerate(self.cards):
            report_index: int = index + 1
            if report_index < len(self.report.forecast_days):
                # Data updates seamlessly because card properties read from its internal saved config
                card.update_data(self.report.forecast_days[report_index])
