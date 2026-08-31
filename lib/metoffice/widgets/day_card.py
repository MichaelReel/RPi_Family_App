import os
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from lib.metoffice.icons import load_stats_icons, load_weather_icons
from lib.metoffice.models import DailyForecastPoint


@dataclass
class UIElementStyle:
    """Holds individual CSS and font properties for a single text label."""
    font_family: str = "Arial, sans-serif"
    font_size: str = "13px"
    font_weight: str = "normal"
    text_color: str = "#888888"

    def to_stylesheet(self) -> str:
        """Generates a valid Qt Style Sheet string from properties."""
        return (
            f"font-family: {self.font_family}; "
            f"font-size: {self.font_size}; "
            f"font-weight: {self.font_weight}; "
            f"color: {self.text_color};"
        )


@dataclass
class CardStyleConfig:
    """Defines the complete visual representation of a weather card instance."""
    # Main Container Styling
    widget_stylesheet: str = (
        "DayCardWidget { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 6px; }"
    )
    
    # Graphic and Layout Sizing
    weather_icon_dim: int = 100
    metric_icon_dim: int = 16
    layout_spacing: int = 6
    row_spacing: int = 8
    
    # Text Element Styles
    date_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(font_size="14px", font_weight="bold", text_color="#0056b3")
    )
    condition_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(font_size="20px", font_weight="500", text_color="#cccccc")
    )
    metrics_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(font_size="13px", text_color="#888888")
    )


class DayCardWidget(QFrame):
    """Displays specific daily weather metrics with decoupled style configurations."""
    
    _icon_cache: dict[int, QPixmap] = {}
    _stats_cache: dict[str, QPixmap] = {}

    def __init__(self, data: DailyForecastPoint, config: CardStyleConfig = None, parent=None) -> None:
        super().__init__(parent)
        
        # Fallback if no specific style object is given
        if config is None:
            self.config = CardStyleConfig()
        else:
            self.config = config
        
        if not DayCardWidget._icon_cache:
            DayCardWidget._icon_cache = load_weather_icons()

        if not DayCardWidget._stats_cache:
            DayCardWidget._stats_cache = load_stats_icons()
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # 1. Initialize main weather elements
        self.lbl_date: QLabel = QLabel()
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_icon: QLabel = QLabel()
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_cond: QLabel = QLabel()
        self.lbl_cond.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 2. Initialize metrics row elements
        self.ico_temp_high: QLabel = QLabel()
        self.lbl_temp_high: QLabel = QLabel()

        self.ico_temp_low: QLabel = QLabel()
        self.lbl_temp_low: QLabel = QLabel()

        self.ico_wind: QLabel = QLabel()
        self.lbl_wind: QLabel = QLabel()
        
        self.ico_feels: QLabel = QLabel()
        self.lbl_feels: QLabel = QLabel()
        
        self.ico_rain: QLabel = QLabel()
        self.lbl_rain: QLabel = QLabel()
        
        self.ico_uv: QLabel = QLabel()
        self.lbl_uv: QLabel = QLabel()
        
        self.ico_temp_high.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ico_temp_low.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ico_wind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ico_feels.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ico_rain.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ico_uv.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_temp_high.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_temp_low.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_wind.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_feels.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_rain.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_uv.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # 3. Build the visual layout skeleton
        layout: QVBoxLayout = QVBoxLayout()
        layout.setSpacing(self.config.layout_spacing)
        layout.addWidget(self.lbl_date)
        layout.addWidget(self.lbl_icon) 
        layout.addWidget(self.lbl_cond)
        layout.addSpacing(4)
        
        def create_metric_row(*args: list[QLabel]) -> QHBoxLayout:
            row = QHBoxLayout()
            row.setSpacing(self.config.row_spacing)
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label: QLabel
            for label in args:
                row.addWidget(label)
            return row

        layout.addLayout(create_metric_row(self.ico_temp_high, self.lbl_temp_high, self.ico_temp_low, self.lbl_temp_low))
        layout.addLayout(create_metric_row(self.ico_wind, self.lbl_wind, self.ico_feels, self.lbl_feels))
        layout.addLayout(create_metric_row(self.ico_rain, self.lbl_rain, self.ico_uv, self.lbl_uv))
        
        self.setLayout(layout)

        # 4. Populate metrics, load images, and apply targeted styling
        self.update_data(data)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter
        from PyQt6.QtWidgets import QStyle, QStyleOption
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)

    def _set_stats_icon(self, label: QLabel, stat_name: str, size: int) -> None:
        pixmap: QPixmap = self._stats_cache[stat_name]
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                size, size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(scaled)
        else:
            label.setText("▪")

    def update_data(self, data: DailyForecastPoint) -> None:
        """Applies configuration data structures directly to UI layouts and controls."""
        
        # Apply configurations from the instance data structure
        self.setStyleSheet(self.config.widget_stylesheet)
        self.lbl_icon.setMinimumSize(self.config.weather_icon_dim, self.config.weather_icon_dim)
        
        # Assign dynamically converted stylesheets
        self.lbl_date.setStyleSheet(self.config.date_style.to_stylesheet())
        self.lbl_cond.setStyleSheet(self.config.condition_style.to_stylesheet())
        
        metrics_css = self.config.metrics_style.to_stylesheet()
        self.lbl_temp_high.setStyleSheet(metrics_css)
        self.lbl_temp_low.setStyleSheet(metrics_css)
        self.lbl_wind.setStyleSheet(metrics_css)
        self.lbl_feels.setStyleSheet(metrics_css)
        self.lbl_rain.setStyleSheet(metrics_css)
        self.lbl_uv.setStyleSheet(metrics_css)
        
        def fmt(val, suffix="") -> str:
            return f"{val}{suffix}" if val is not None else "--"

        self.lbl_date.setText(data.date.strftime("%A, %b %d"))
        self.lbl_cond.setText(data.weather_condition)
        
        self.lbl_temp_high.setText(f"{fmt(data.max_temperature_c, '°C')}")
        self.lbl_temp_low.setText(f"{fmt(data.min_temperature_c, '°C')}")
        self.lbl_wind.setText(f"{fmt(data.wind_speed_midday_mph, 'mph')}")
        self.lbl_feels.setText(fmt(data.max_feels_like_c, "°C"))
        self.lbl_rain.setText(fmt(data.rain_probability_pct, "%"))
        self.lbl_uv.setText(fmt(data.uv_index_max))

        # Size mapping via configuration properties
        metric_dim = self.config.metric_icon_dim
        self._set_stats_icon(self.ico_temp_high, "temp_high", size=metric_dim)
        self._set_stats_icon(self.ico_temp_low, "temp_low", size=metric_dim)
        self._set_stats_icon(self.ico_wind, "wind", size=metric_dim)
        self._set_stats_icon(self.ico_feels, "temp_feel", size=metric_dim)
        self._set_stats_icon(self.ico_rain, "rain_pct", size=metric_dim)
        self._set_stats_icon(self.ico_uv, "uv_index", size=metric_dim)

        weather_code = getattr(data, "weather_code", None)
        pixmap = self._icon_cache.get(weather_code)

        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.config.weather_icon_dim, self.config.weather_icon_dim, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_icon.setPixmap(scaled_pixmap)
        else:
            self.lbl_icon.setText("❓")
