"""Widget that renders a multi-lane weather stats chart of the next 7 days."""
from logging import Logger, getLogger
from typing import Final

from PyQt6.QtCore import QRectF, Qt, QRect
from PyQt6.QtGui import QColor, QPen, QPainter, QFont, QBrush, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from collections.abc import Callable
from lib.metoffice.icons import load_stats_icons
from lib.metoffice.models import DailyForecastPoint, HourlyForecastPoint, HumanReadableWeatherReport

_LOGGER: Final[Logger] = getLogger(__name__)

# Series colours
_TEMP_MAX_COLOR = "#FF6B6B"
_TEMP_MIN_COLOR = "#4D96FF"
_FEELS_LIKE_COLOR = "#FFB347"
_RAIN_COLOR = "#4ECDC4"
_UV_COLOR = "#FFD93D"
_WIND_COLOR = "#95E1D3"

_AXIS_COLOR = "#555555"
_TEXT_COLOR = "#cccccc"
_GRID_COLOR = "#333355"
_LANE_BORDER_COLOR = "#444466"

# Fixed UV axis range (WHO UV index scale 0–11)
_UV_AXIS_MAX: Final[float] = 11.0

# Layout dimensions
_ICON_SIZE: Final[int] = 28        # icon pixel size
_ICON_BORDER: Final[int] = 2      # border width around icons
_LEFT_MARGIN: Final[int] = 90     # total left margin: icons + gap + Y-axis labels
_RIGHT_MARGIN: Final[int] = 12
_TOP_PADDING: Final[int] = 14     # padding above chart area (so top labels aren't clipped)
_BOTTOM_PADDING: Final[int] = 12  # padding below chart area


def _load_lane_icons() -> dict[str, QPixmap]:
    """Load the stats icons once and return a dict keyed by stat name."""
    try:
        return load_stats_icons()
    except Exception:
        _LOGGER.exception("Failed to load stats icons for weather graph lanes")
        return {}


class _LaneFrame(QFrame):
    """A single lane frame that delegates painting to a parent-provided callback."""

    def __init__(self, paint_fn: Callable[[QPainter, int, int], None], bg_color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._paint_fn = paint_fn
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(0)
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg_color}; border: 0px; }}"
        )
        self.setMinimumHeight(80)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_fn(painter, self.width(), self.height())
        painter.end()


class WeatherGraphWidget(QWidget):
    """Renders a multi-lane chart of the next 7 days of weather stats.

    Lanes (top to bottom):
    - Max, Min & Feels-like Temperature (C)
    - Rain Probability (%)
    - UV Index (bar chart)
    - Wind Speed (mph)
    """

    def __init__(
        self,
        report_source: Callable[[], HumanReadableWeatherReport],
        bg_color: str = "#000022",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bg_color = bg_color
        self._report_source = report_source
        self._days: list[DailyForecastPoint] = []
        self._hourly: list[HourlyForecastPoint] = []
        self._lane_icons: dict[str, QPixmap] = _load_lane_icons()

        self.setStyleSheet(f"WeatherGraphWidget {{ background-color: {bg_color}; }}")

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 28)  # extra bottom space for date labels
        layout.setSpacing(6)
        self.setLayout(layout)

        # Title
        self._title = QLabel("7-Day Forecast")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            f"QLabel {{ background-color: transparent; color: {_TEXT_COLOR}; "
            f"font-size: 22px; font-weight: bold; font-family: Arial, sans-serif; }}"
        )
        layout.addWidget(self._title)

        # Lane frames
        self._temp_frame = _LaneFrame(self._paint_temp_lane, bg_color)
        self._rain_frame = _LaneFrame(self._paint_rain_lane, bg_color)
        self._uv_frame = _LaneFrame(self._paint_uv_lane, bg_color)
        self._wind_frame = _LaneFrame(self._paint_wind_lane, bg_color)

        self._frames = [self._temp_frame, self._rain_frame, self._uv_frame, self._wind_frame]
        for frame in self._frames:
            layout.addWidget(frame, 1)

        self.setMinimumSize(400, 400)
        self._refresh()

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        try:
            report = self._report_source()
        except Exception:
            _LOGGER.exception("Error fetching weather report for graph")
            self._days = []
            self._repaint()
            return

        if report is None:
            _LOGGER.error("No weather report available for graph")
            self._days = []
            self._repaint()
            return

        self._days = report.forecast_days[1:8]
        self._hourly = report.forecast_hourly
        self._repaint()

    def _repaint(self) -> None:
        for frame in self._frames:
            frame.update()

    # ------------------------------------------------------------------
    # Shared drawing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_temp_range(days: list[DailyForecastPoint]) -> tuple[float, float]:
        all_vals: list[float] = []
        for d in days:
            if d.max_temperature_c is not None:
                all_vals.append(float(d.max_temperature_c))
            if d.min_temperature_c is not None:
                all_vals.append(float(d.min_temperature_c))
            if d.max_feels_like_c is not None:
                all_vals.append(float(d.max_feels_like_c))
        if not all_vals:
            return 0.0, 1.0
        v_min = min(all_vals) - 1.0
        v_max = max(all_vals) + 1.0
        if v_max == v_min:
            v_max = v_min + 1.0
        return v_min, v_max

    def _draw_lane(
        self,
        painter: QPainter,
        width: int,
        height: int,
        series: list[tuple[list, str]],
        v_min: float,
        v_max: float,
        unit: str,
        bar_mode: bool = False,
        icons: list[tuple[str, str]] | None = None,  # [(icon_key, border_color), ...]
    ) -> None:
        self._draw_lane_impl(painter, width, height, series, v_min, v_max, unit, self._days, len(self._days), bar_mode, icons)

    def _draw_lane_hourly(
        self,
        painter: QPainter,
        width: int,
        height: int,
        series: list[tuple[list, str]],
        v_min: float,
        v_max: float,
        unit: str,
        bar_mode: bool = False,
        icons: list[tuple[str, str]] | None = None,
    ) -> None:
        self._draw_lane_impl(painter, width, height, series, v_min, v_max, unit, self._hourly, len(self._hourly), bar_mode, icons)

    def _draw_lane_impl(
        self,
        painter: QPainter,
        width: int,
        height: int,
        series: list[tuple[list, str]],
        v_min: float,
        v_max: float,
        unit: str,
        data_points: list,
        n: int,
        bar_mode: bool = False,
        icons: list[tuple[str, str]] | None = None,
    ) -> None:
        if n == 0:
            painter.setPen(QPen(QColor(_TEXT_COLOR), 1))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(
                QRectF(0, 0, width, height),
                Qt.AlignmentFlag.AlignCenter,
                "No data available",
            )
            return

        # --- Lane icons (left of Y-axis labels) ---
        if icons:
            icon_total = _ICON_SIZE + _ICON_BORDER * 2
            icon_x = 4
            if len(icons) == 1:
                y_offsets = [height / 2]
            else:
                y_offsets = [height * (i + 1) / (len(icons) + 1) for i in range(len(icons))]

            for (icon_key, border_color), cy in zip(icons, y_offsets):
                pixmap = self._lane_icons.get(icon_key)
                if pixmap is None or pixmap.isNull():
                    continue
                y = int(cy - icon_total / 2)
                # Border
                painter.setPen(QPen(QColor(border_color), _ICON_BORDER))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRect(icon_x, y, icon_total, icon_total)
                # Icon centred inside border
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                target_size = icon_total - _ICON_BORDER * 2
                scaled = pixmap.scaled(
                    target_size, target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                draw_x = icon_x + _ICON_BORDER + (target_size - scaled.width()) // 2
                draw_y = y + _ICON_BORDER + (target_size - scaled.height()) // 2
                painter.drawPixmap(QRect(draw_x, draw_y, scaled.width(), scaled.height()), scaled)

        # --- Chart geometry ---
        chart_left = _LEFT_MARGIN
        chart_right = width - _RIGHT_MARGIN
        chart_width = chart_right - chart_left
        plot_top = _TOP_PADDING
        plot_bottom = height - _BOTTOM_PADDING
        plot_height = plot_bottom - plot_top

        # Grid lines + Y-axis labels (3 lines: min, mid, max)
        painter.setFont(QFont("Arial", 9))
        for i in range(3):
            ratio = i / 2
            y = plot_bottom - (plot_height * ratio)
            painter.setPen(QPen(QColor(_GRID_COLOR), 1))
            painter.drawLine(int(chart_left), int(y), int(chart_right), int(y))

            val = v_min + (v_max - v_min) * ratio
            if unit == "C":
                label = f"{val:.0f}\u00b0C"
            elif unit == "%":
                label = f"{val:.0f}%"
            else:
                label = f"{val:.0f}"

            painter.setPen(QPen(QColor(_TEXT_COLOR), 1))
            label_rect = QRectF(4, y - 8, _LEFT_MARGIN - 8, 16)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        # Bottom axis
        painter.setPen(QPen(QColor(_AXIS_COLOR), 1))
        painter.drawLine(int(chart_left), int(plot_bottom), int(chart_right), int(plot_bottom))

        # X/Y position helpers
        def x_pos(i: int) -> float:
            if n == 1:
                return chart_left + chart_width / 2
            return chart_left + (chart_width * i) / (n - 1)

        def y_pos(value: float) -> float:
            ratio = (value - v_min) / (v_max - v_min)
            return plot_bottom - (plot_height * ratio)

        # Draw each series
        for vals, color in series:
            if bar_mode:
                self._draw_bars(painter, vals, color, x_pos, y_pos, plot_bottom, chart_width)
            else:
                self._draw_line(painter, vals, color, x_pos, y_pos)

    @staticmethod
    def _draw_line(painter: QPainter, vals: list, color: str, x_pos, y_pos) -> None:
        points: list[tuple[float, float]] = []
        for i, val in enumerate(vals):
            if val is not None:
                points.append((x_pos(i), y_pos(float(val))))

        if not points:
            return

        if len(points) >= 2:
            painter.setPen(QPen(QColor(color), 2))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]), int(points[i + 1][0]), int(points[i + 1][1]))

        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(QPen(QColor(color), 1))
        for px, py in points:
            painter.drawEllipse(int(px) - 3, int(py) - 3, 6, 6)

    @staticmethod
    def _draw_bars(painter: QPainter, vals: list, color: str, x_pos, y_pos, base_y: float, chart_width: float) -> None:
        n = len(vals)
        bar_width = max(10, min(36, (chart_width / max(n, 1)) * 0.55))
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(QPen(QColor(color), 1))

        for i, val in enumerate(vals):
            if val is None:
                continue
            x = x_pos(i) - bar_width / 2
            bar_top = y_pos(float(val))
            bar_h = base_y - bar_top
            if bar_h < 2:
                bar_h = 2
            painter.drawRoundedRect(int(x), int(bar_top), int(bar_width), int(bar_h), 3, 3)

    # ------------------------------------------------------------------
    # Per-lane paint callbacks (called by _LaneFrame.paintEvent)
    # ------------------------------------------------------------------

    def _paint_temp_lane(self, painter: QPainter, width: int, height: int) -> None:
        v_min, v_max = self._compute_temp_range(self._days)
        series = [
            ([d.max_temperature_c for d in self._days], _TEMP_MAX_COLOR),
            ([d.min_temperature_c for d in self._days], _TEMP_MIN_COLOR),
            ([d.max_feels_like_c for d in self._days], _FEELS_LIKE_COLOR),
        ]
        icons = [
            ("temp_high", _TEMP_MAX_COLOR),
            ("temp_feel", _FEELS_LIKE_COLOR),
            ("temp_low", _TEMP_MIN_COLOR),
        ]
        self._draw_lane(painter, width, height, series, v_min, v_max, unit="C", icons=icons)

    def _paint_rain_lane(self, painter: QPainter, width: int, height: int) -> None:
        if self._hourly:
            series = [([h.prob_of_precipitation_pct for h in self._hourly], _RAIN_COLOR)]
            icons = [("rain_pct", _RAIN_COLOR)]
            self._draw_lane_hourly(painter, width, height, series, 0.0, 100.0, unit="%", icons=icons)
        else:
            series = [([d.rain_probability_pct for d in self._days], _RAIN_COLOR)]
            icons = [("rain_pct", _RAIN_COLOR)]
            self._draw_lane(painter, width, height, series, 0.0, 100.0, unit="%", icons=icons)

    def _paint_uv_lane(self, painter: QPainter, width: int, height: int) -> None:
        if self._hourly:
            series = [([h.uv_index for h in self._hourly], _UV_COLOR)]
            icons = [("uv_index", _UV_COLOR)]
            self._draw_lane_hourly(painter, width, height, series, 0.0, _UV_AXIS_MAX, unit="", bar_mode=True, icons=icons)
        else:
            series = [([d.uv_index_max for d in self._days], _UV_COLOR)]
            icons = [("uv_index", _UV_COLOR)]
            self._draw_lane(painter, width, height, series, 0.0, _UV_AXIS_MAX, unit="", bar_mode=True, icons=icons)

    def _paint_wind_lane(self, painter: QPainter, width: int, height: int) -> None:
        series = [([d.wind_speed_midday_mph for d in self._days], _WIND_COLOR)]
        icons = [("wind", _WIND_COLOR)]
        v_max = max(
            (float(d.wind_speed_midday_mph) for d in self._days if d.wind_speed_midday_mph is not None),
            default=20.0,
        ) + 5.0
        self._draw_lane(painter, width, height, series, 0.0, v_max, unit="mph", icons=icons)

    # ------------------------------------------------------------------
    # Date labels (painted at the bottom of the main widget)
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._days:
            self._draw_date_labels(painter)

        painter.end()

    def _draw_date_labels(self, painter: QPainter) -> None:
        n = len(self._days)
        w = self.width()
        left_margin = _LEFT_MARGIN
        right_margin = _RIGHT_MARGIN
        chart_width = w - left_margin - right_margin

        painter.setPen(QPen(QColor(_TEXT_COLOR), 1))
        painter.setFont(QFont("Arial", 10))

        # Place labels in the 28px bottom strip (below the last lane frame)
        y = self.height() - 22
        for i, day in enumerate(self._days):
            if n == 1:
                x = left_margin + chart_width / 2
            else:
                x = left_margin + (chart_width * i) / (n - 1)
            label = day.date.strftime("%a %d")
            painter.drawText(int(x) - 30, y, 60, 16, Qt.AlignmentFlag.AlignCenter, label)
