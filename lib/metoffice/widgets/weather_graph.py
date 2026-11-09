"""Widget that renders a multi-lane weather stats chart of the next 7 days."""
from logging import Logger, getLogger
from typing import Final

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPen, QPainter, QFont, QBrush
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from collections.abc import Callable
from lib.metoffice.models import DailyForecastPoint, HumanReadableWeatherReport

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


class _LaneFrame(QFrame):
    """A single lane frame that delegates painting to a parent-provided callback."""

    def __init__(self, paint_fn: Callable[[QPainter, int, int], None], bg_color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._paint_fn = paint_fn
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(1)
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg_color}; border: 1px solid {_LANE_BORDER_COLOR}; }}"
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
    ) -> None:
        n = len(self._days)
        if n == 0:
            painter.setPen(QPen(QColor(_TEXT_COLOR), 1))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(
                QRectF(0, 0, width, height),
                Qt.AlignmentFlag.AlignCenter,
                "No data available",
            )
            return

        y_axis_width = 44
        chart_left = y_axis_width
        chart_right = width - 4
        chart_width = chart_right - chart_left

        # Grid lines + Y-axis labels (3 lines: min, mid, max)
        painter.setFont(QFont("Arial", 9))
        for i in range(3):
            ratio = i / 2
            y = height - (height * ratio)
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
            label_rect = QRectF(0, y - 8, y_axis_width - 4, 16)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        # Bottom axis
        painter.setPen(QPen(QColor(_AXIS_COLOR), 1))
        painter.drawLine(int(chart_left), int(height), int(chart_right), int(height))

        # X/Y position helpers (closures capturing local scope)
        def x_pos(i: int) -> float:
            if n == 1:
                return chart_left + chart_width / 2
            return chart_left + (chart_width * i) / (n - 1)

        def y_pos(value: float) -> float:
            ratio = (value - v_min) / (v_max - v_min)
            return height - (height * ratio)

        # Draw each series
        for vals, color in series:
            if bar_mode:
                self._draw_bars(painter, vals, color, x_pos, y_pos, height, chart_width)
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
        self._draw_lane(painter, width, height, series, v_min, v_max, unit="C")

    def _paint_rain_lane(self, painter: QPainter, width: int, height: int) -> None:
        series = [([d.rain_probability_pct for d in self._days], _RAIN_COLOR)]
        self._draw_lane(painter, width, height, series, 0.0, 100.0, unit="%")

    def _paint_uv_lane(self, painter: QPainter, width: int, height: int) -> None:
        series = [([d.uv_index_max for d in self._days], _UV_COLOR)]
        v_max = max((float(d.uv_index_max) for d in self._days if d.uv_index_max is not None), default=10.0) + 1.0
        self._draw_lane(painter, width, height, series, 0.0, v_max, unit="", bar_mode=True)

    def _paint_wind_lane(self, painter: QPainter, width: int, height: int) -> None:
        series = [([d.wind_speed_midday_mph for d in self._days], _WIND_COLOR)]
        v_max = max(
            (float(d.wind_speed_midday_mph) for d in self._days if d.wind_speed_midday_mph is not None),
            default=20.0,
        ) + 5.0
        self._draw_lane(painter, width, height, series, 0.0, v_max, unit="mph")

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
        left_margin = 44
        right_margin = 4
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
