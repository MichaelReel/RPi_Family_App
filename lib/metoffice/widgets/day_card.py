from dataclasses import dataclass, field
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPaintEvent, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QStyle,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)

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
    widget_stylesheet: str = "DayCardWidget { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 6px; }"

    # Graphic and Layout Sizing
    weather_icon_dim: int = 100
    metric_icon_dim: int = 16
    layout_spacing: int = 6
    row_spacing: int = 8

    # Text Element Styles
    date_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(
            font_size="14px", font_weight="bold", text_color="#0056b3"
        )
    )
    condition_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(
            font_size="20px", font_weight="500", text_color="#cccccc"
        )
    )
    metrics_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(font_size="13px", text_color="#888888")
    )


class DayCardWidget(QFrame):
    """Displays specific daily weather metrics with decoupled style configurations."""

    # Icon caches are shared across all DayCardWidget instances via a singleton
    # to avoid reloading the same icon files on each widget creation.
    _icon_cache: dict[int, QPixmap] = {}
    _stats_cache: dict[str, QPixmap] = {}

    def __init__(
        self,
        data: DailyForecastPoint,
        config: CardStyleConfig | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        # Fallback if no specific style object is given
        self._style_config: CardStyleConfig = (
            config if config is not None else CardStyleConfig()
        )

        if not DayCardWidget._icon_cache:
            DayCardWidget._icon_cache = load_weather_icons()

        if not DayCardWidget._stats_cache:
            DayCardWidget._stats_cache = load_stats_icons()

        self.setFrameShape(QFrame.Shape.StyledPanel)

        # 1. Initialize main weather elements
        self._label_date: QLabel = QLabel()
        self._label_date.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label_icon: QLabel = QLabel()
        self._label_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label_cond: QLabel = QLabel()
        self._label_cond.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. Initialize metrics row elements
        self._icon_temp_high: QLabel = QLabel()
        self._label_temp_high: QLabel = QLabel()

        self._icon_temp_low: QLabel = QLabel()
        self._label_temp_low: QLabel = QLabel()

        self._icon_wind: QLabel = QLabel()
        self._label_wind: QLabel = QLabel()

        self._icon_feels: QLabel = QLabel()
        self._label_feels: QLabel = QLabel()

        self._icon_rain: QLabel = QLabel()
        self._label_rain: QLabel = QLabel()

        self._icon_uv: QLabel = QLabel()
        self._label_uv: QLabel = QLabel()

        self._icon_temp_high.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_temp_low.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_wind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_feels.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_rain.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_uv.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label_temp_high.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._label_temp_low.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._label_wind.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._label_feels.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._label_rain.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._label_uv.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # 3. Build the visual layout skeleton
        layout: QVBoxLayout = QVBoxLayout()
        layout.setSpacing(self._style_config.layout_spacing)
        layout.addWidget(self._label_date)
        layout.addWidget(self._label_icon)
        layout.addWidget(self._label_cond)
        layout.addSpacing(4)

        def create_metric_row(*args: QLabel) -> QHBoxLayout:
            row = QHBoxLayout()
            row.setSpacing(self._style_config.row_spacing)
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label: QLabel
            for label in args:
                row.addWidget(label)
            return row

        layout.addLayout(
            create_metric_row(
                self._icon_temp_high,
                self._label_temp_high,
                self._icon_temp_low,
                self._label_temp_low,
            )
        )
        layout.addLayout(
            create_metric_row(
                self._icon_wind, self._label_wind, self._icon_feels, self._label_feels
            )
        )
        layout.addLayout(
            create_metric_row(self._icon_rain, self._label_rain, self._icon_uv, self._label_uv)
        )

        self.setLayout(layout)

        # 4. Populate metrics, load images, and apply targeted styling
        self.update_data(data)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        style = self.style()
        if style is not None:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)

    def _set_stats_icon(self, label: QLabel, stat_name: str, size: int) -> None:
        pixmap: QPixmap = self._stats_cache[stat_name]
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            label.setPixmap(scaled)
        else:
            label.setText("▪")

    def update_data(self, data: DailyForecastPoint) -> None:
        """Applies configuration data structures directly to UI layouts and controls."""

        # Apply configurations from the instance data structure
        self.setStyleSheet(self._style_config.widget_stylesheet)
        self._label_icon.setMinimumSize(
            self._style_config.weather_icon_dim, self._style_config.weather_icon_dim
        )

        # Assign dynamically converted stylesheets
        self._label_date.setStyleSheet(self._style_config.date_style.to_stylesheet())
        self._label_cond.setStyleSheet(self._style_config.condition_style.to_stylesheet())

        metrics_css = self._style_config.metrics_style.to_stylesheet()
        self._label_temp_high.setStyleSheet(metrics_css)
        self._label_temp_low.setStyleSheet(metrics_css)
        self._label_wind.setStyleSheet(metrics_css)
        self._label_feels.setStyleSheet(metrics_css)
        self._label_rain.setStyleSheet(metrics_css)
        self._label_uv.setStyleSheet(metrics_css)

        def fmt(val: Decimal | int | None, suffix: str = "") -> str:
            return f"{val}{suffix}" if val is not None else "--"

        self._label_date.setText(data.date.strftime("%A, %b %d"))
        self._label_cond.setText(data.weather_condition)

        self._label_temp_high.setText(f"{fmt(data.max_temperature_c, '°C')}")
        self._label_temp_low.setText(f"{fmt(data.min_temperature_c, '°C')}")
        self._label_wind.setText(f"{fmt(data.wind_speed_midday_mph, 'mph')}")
        self._label_feels.setText(fmt(data.max_feels_like_c, "°C"))
        self._label_rain.setText(fmt(data.rain_probability_pct, "%"))
        self._label_uv.setText(fmt(data.uv_index_max))

        # Size mapping via configuration properties
        metric_dim = self._style_config.metric_icon_dim
        self._set_stats_icon(self._icon_temp_high, "temp_high", size=metric_dim)
        self._set_stats_icon(self._icon_temp_low, "temp_low", size=metric_dim)
        self._set_stats_icon(self._icon_wind, "wind", size=metric_dim)
        self._set_stats_icon(self._icon_feels, "temp_feel", size=metric_dim)
        self._set_stats_icon(self._icon_rain, "rain_pct", size=metric_dim)
        self._set_stats_icon(self._icon_uv, "uv_index", size=metric_dim)

        weather_code = data.weather_code
        pixmap: QPixmap | None = (
            self._icon_cache.get(weather_code) if weather_code is not None else None
        )

        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self._style_config.weather_icon_dim,
                self._style_config.weather_icon_dim,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._label_icon.setPixmap(scaled_pixmap)
        else:
            self._label_icon.setText("❓")
