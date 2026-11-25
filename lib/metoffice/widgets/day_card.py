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

from config.ui import CardStyleConfig, UIElementStyle
from lib.metoffice.icons import load_stats_icons, load_weather_icons
from lib.metoffice.models import DailyForecastPoint

__all__ = ["CardStyleConfig", "DayCardWidget", "UIElementStyle"]


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

        self._initialise_icon_caches()

        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._build_main_labels()
        self._build_metric_labels()
        self._apply_metric_alignments()
        self._build_layout()

        # 4. Populate metrics, load images, and apply targeted styling
        self.update_data(data)

    def _initialise_icon_caches(self) -> None:
        """Populates the shared class-level icon caches on first use."""
        if not DayCardWidget._icon_cache:
            DayCardWidget._icon_cache = load_weather_icons()

        if not DayCardWidget._stats_cache:
            DayCardWidget._stats_cache = load_stats_icons()

    def _build_main_labels(self) -> None:
        """Creates the main date, weather-icon and condition labels."""
        self._label_date: QLabel = QLabel()
        self._label_date.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label_icon: QLabel = QLabel()
        self._label_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label_cond: QLabel = QLabel()
        self._label_cond.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _build_metric_labels(self) -> None:
        """Creates the icon and text label pairs for each metric in the rows."""
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

    def _apply_metric_alignments(self) -> None:
        """Aligns the metric icons to centre and the metric text to the left."""
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

    def _build_layout(self) -> None:
        """Assembles the main labels and metric rows into the card layout."""
        layout: QVBoxLayout = QVBoxLayout()
        layout.setSpacing(self._style_config.layout_spacing)
        layout.addWidget(self._label_date)
        layout.addWidget(self._label_icon)
        layout.addWidget(self._label_cond)
        layout.addSpacing(4)

        layout.addLayout(
            self._build_metric_row(
                self._icon_temp_high,
                self._label_temp_high,
                self._icon_temp_low,
                self._label_temp_low,
            )
        )
        layout.addLayout(
            self._build_metric_row(
                self._icon_wind, self._label_wind, self._icon_feels, self._label_feels
            )
        )
        layout.addLayout(
            self._build_metric_row(
                self._icon_rain, self._label_rain, self._icon_uv, self._label_uv
            )
        )

        self.setLayout(layout)

    def _build_metric_row(self, *args: QLabel) -> QHBoxLayout:
        """Builds a centred horizontal row from the given labels."""
        row = QHBoxLayout()
        row.setSpacing(self._style_config.row_spacing)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label: QLabel
        for label in args:
            row.addWidget(label)
        return row

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
        self._apply_style()
        self._apply_texts(data)
        self._apply_icons(data)

    def _fmt(self, val: Decimal | int | None, suffix: str = "") -> str:
        """Formats a metric value, returning a dash when the value is absent."""
        return f"{val}{suffix}" if val is not None else "--"

    def _apply_style(self) -> None:
        """Applies the stylesheet and icon sizing from the style configuration."""
        self.setStyleSheet(self._style_config.widget_stylesheet)
        self._label_icon.setMinimumSize(
            self._style_config.weather_icon_dim, self._style_config.weather_icon_dim
        )

        self._label_date.setStyleSheet(self._style_config.date_style.to_stylesheet())
        self._label_cond.setStyleSheet(
            self._style_config.condition_style.to_stylesheet()
        )

        metrics_css = self._style_config.metrics_style.to_stylesheet()
        self._label_temp_high.setStyleSheet(metrics_css)
        self._label_temp_low.setStyleSheet(metrics_css)
        self._label_wind.setStyleSheet(metrics_css)
        self._label_feels.setStyleSheet(metrics_css)
        self._label_rain.setStyleSheet(metrics_css)
        self._label_uv.setStyleSheet(metrics_css)

    def _apply_texts(self, data: DailyForecastPoint) -> None:
        """Populates the date, condition and metric labels from the data point."""
        self._label_date.setText(data.date.strftime("%A, %b %d"))
        self._label_cond.setText(data.weather_condition)

        self._label_temp_high.setText(f"{self._fmt(data.max_temperature_c, '°C')}")
        self._label_temp_low.setText(f"{self._fmt(data.min_temperature_c, '°C')}")
        self._label_wind.setText(f"{self._fmt(data.wind_speed_midday_mph, 'mph')}")
        self._label_feels.setText(self._fmt(data.max_feels_like_c, "°C"))
        self._label_rain.setText(self._fmt(data.rain_probability_pct, "%"))
        self._label_uv.setText(self._fmt(data.uv_index_max))

    def _apply_icons(self, data: DailyForecastPoint) -> None:
        """Loads the weather and stats icons for the given data point."""
        metric_dim = self._style_config.metric_icon_dim
        self._set_stats_icon(self._icon_temp_high, "temp_high", size=metric_dim)
        self._set_stats_icon(self._icon_temp_low, "temp_low", size=metric_dim)
        self._set_stats_icon(self._icon_wind, "wind", size=metric_dim)
        self._set_stats_icon(self._icon_feels, "temp_feel", size=metric_dim)
        self._set_stats_icon(self._icon_rain, "rain_pct", size=metric_dim)
        self._set_stats_icon(self._icon_uv, "uv_index", size=metric_dim)

        self._set_weather_icon(data.weather_code)

    def _set_weather_icon(self, weather_code: int | None) -> None:
        """Loads the weather icon for a code, falling back to a placeholder."""
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
