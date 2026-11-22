"""Widget that renders a multi-lane weather stats chart of the next 8 days."""

import math
from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal
from logging import Logger, getLogger
from typing import Final
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QRect, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPaintEvent, QPen, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from lib.metoffice.icons import load_stats_icons
from lib.metoffice.models import (
    DailyForecastPoint,
    HourlyForecastPoint,
    HumanReadableWeatherReport,
    ThreeHourlyForecastPoint,
)

_LOGGER: Final[Logger] = getLogger(__name__)

# Series colours
_TEMP_MAX_COLOR = "#FF6B6B"
_TEMP_MIN_COLOR = "#4D96FF"
_FEELS_LIKE_COLOR = "#FFB347"
_RAIN_COLOR = "#4ECDC4"
_UV_COLOR = "#FFD93D"
_WIND_COLOR = "#95E1D3"
_WIND_GUST_COLOR = "#FFFFFF"

_AXIS_COLOR = "#555555"
_TEXT_COLOR = "#cccccc"
_GRID_COLOR = "#333355"
_GRID_COLOR_STRONG = (
    "#6A6A9A"  # bold 0°C reference line (slightly bolder/brighter than _GRID_COLOR)
)
_LANE_BORDER_COLOR = "#444466"
# Vertical reference lines: faint midnight gridlines and a distinct "now" marker.
_MIDNIGHT_COLOR = "#3A3A5C"
_NOW_COLOR = "#E86A5E"

# The temperature lane's unit string (distinguishes °C lanes from %/mph lanes).
_TEMP_UNIT: Final[str] = "C"

# Layout dimensions
_ICON_SIZE: Final[int] = 28  # icon pixel size
_ICON_BORDER: Final[int] = 2  # border width around icons
_LEFT_MARGIN: Final[int] = 90  # total left margin: icons + gap + Y-axis labels
_RIGHT_MARGIN: Final[int] = 12
_TOP_PADDING: Final[int] = 14  # padding above chart area (so top labels aren't clipped)
_BOTTOM_PADDING: Final[int] = 12  # padding below chart area
# Inset the first data point away from the Y-axis so the dot/line doesn't
# overdraw the axis line or labels.
_DATA_LEFT_INSET: Final[int] = 10


def _load_lane_icons() -> dict[str, QPixmap]:
    """Load the stats icons once and return a dict keyed by stat name."""
    try:
        return load_stats_icons()
    except Exception:
        _LOGGER.exception("Failed to load stats icons for weather graph lanes")
        return {}


class _LaneFrame(QFrame):
    """A single lane frame that delegates painting to a parent-provided callback."""

    def __init__(
        self,
        paint_fn: Callable[[QPainter, int, int], None],
        bg_color: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._paint_fn = paint_fn
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(0)
        self.setStyleSheet(f"QFrame {{ background-color: {bg_color}; border: 0px; }}")
        self.setMinimumHeight(80)

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_fn(painter, self.width(), self.height())
        painter.end()


class WeatherGraphWidget(QWidget):
    """Renders a multi-lane chart of the coming days of weather stats.

    Lanes (top to bottom):
    - Temperature (C): min, max and feels-like, each as one continuous line
      built from the dense 1-hourly points then the coarser 3-hourly points.
    - Rain probability (%) and UV index: two independent sub-axes side by side,
      each a continuous line.
    - Wind (mph): average speed and gust, each a continuous line.
    """

    def __init__(
        self,
        report_source: Callable[[], HumanReadableWeatherReport | None],
        bg_color: str = "#000022",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._bg_color = bg_color
        self._report_source: Callable[[], HumanReadableWeatherReport | None] = (
            report_source
        )
        self._days: list[DailyForecastPoint] = []
        self._hourly: list[HourlyForecastPoint] = []
        self._three_hourly: list[ThreeHourlyForecastPoint] = []
        self._lane_icons: dict[str, QPixmap] = _load_lane_icons()

        self.setStyleSheet(f"WeatherGraphWidget {{ background-color: {bg_color}; }}")

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 28)  # extra bottom space for date labels
        layout.setSpacing(6)
        self.setLayout(layout)

        layout.addWidget(self._build_title())

        for frame in self._build_lanes():
            layout.addWidget(frame, 1)

        self.setMinimumSize(400, 400)
        self._refresh()

    def _build_title(self) -> QLabel:
        """Builds the centred "8-Day Forecast" title label for the chart."""
        title = QLabel("8-Day Forecast")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"QLabel {{ background-color: transparent; color: {_TEXT_COLOR}; "
            f"font-size: 22px; font-weight: bold; font-family: Arial, sans-serif; }}"
        )
        return title

    def _build_lanes(self) -> list[_LaneFrame]:
        """Builds the temperature, rain/UV and wind lane frames (top to bottom)."""
        temp_frame = _LaneFrame(self._paint_temp_lane, self._bg_color)
        rain_uv_frame = _LaneFrame(self._paint_rain_uv_lane, self._bg_color)
        wind_frame = _LaneFrame(self._paint_wind_lane, self._bg_color)

        self._frames = [temp_frame, rain_uv_frame, wind_frame]
        return self._frames

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        try:
            report = self._report_source()
        except Exception:
            _LOGGER.exception("Error fetching weather report for graph")
            self._days = []
            self._hourly = []
            self._three_hourly = []
            self._repaint()
            return

        if report is None:
            _LOGGER.error("No weather report available for graph")
            self._days = []
            self._hourly = []
            self._three_hourly = []
            self._repaint()
            return

        self._days = report.forecast_days[
            1:8
        ]  # the 7 days the daily API provides (today is index 0)
        self._hourly = report.forecast_hourly
        self._three_hourly = report.forecast_three_hourly or []
        self._extend_labels_to_fine_window()
        self._repaint()

    def _extend_labels_to_fine_window(self) -> None:
        """Add a date label for the next day when the plotted fine-data window
        extends a full extra day beyond the last daily label.

        The daily API only returns today + 7 days, but the 3-hourly series runs
        ~8 days out, so the 8th day (same weekday next week) is drawn on the
        graph without a label. Derive that day's date from the fine-data end so
        the X-axis covers every day that is mostly displayed.
        """
        if not self._hourly and not self._three_hourly:
            return
        if not self._days:
            return
        window_start, window_end = self._time_window()
        last_label = self._days[-1].date
        # The plotted window must extend at least a day past the last label for
        # the next day to be meaningfully (mostly) drawn.
        if window_end <= last_label + timedelta(days=1):
            return
        extra = DailyForecastPoint(
            date=last_label + timedelta(days=1),
            max_temperature_c=None,
            min_temperature_c=None,
            max_feels_like_c=None,
            rain_probability_pct=None,
            snow_probability_pct=None,
            wind_speed_midday_mph=None,
            wind_direction_midday_deg=None,
            visibility_midday_metres=None,
            uv_index_max=None,
            weather_code=None,
            weather_condition="",
        )
        self._days.append(extra)

    def _repaint(self) -> None:
        for frame in self._frames:
            frame.update()

    # ------------------------------------------------------------------
    # Series construction (dense hourly -> coarser three-hourly, deduped)
    # ------------------------------------------------------------------

    @staticmethod
    def _continuous_series(
        hourly: list[HourlyForecastPoint],
        three_hourly: list[ThreeHourlyForecastPoint],
        hourly_getter: Callable[[HourlyForecastPoint], float | None],
        three_hourly_getter: Callable[[ThreeHourlyForecastPoint], float | None],
    ) -> list[tuple[datetime, float | None]]:
        """Build one time-ordered series by stitching dense hourly points onto
        the coarser three-hourly points.

        Hourly points always take precedence: a three-hourly point whose
        timestamp already appears among the hourly points is dropped so the two
        series never overlap. The result is sorted by time.
        """
        series: list[tuple[datetime, float | None]] = []
        hourly_times: set[datetime] = set()
        for hp in hourly:
            series.append((hp.time, hourly_getter(hp)))
            hourly_times.add(hp.time)

        for thp in three_hourly:
            if thp.time in hourly_times:
                continue  # hourly data takes precedence at shared timestamps
            series.append((thp.time, three_hourly_getter(thp)))

        series.sort(key=lambda item: item[0])
        return series

    # ------------------------------------------------------------------
    # Time-window / x-positioning helpers
    # ------------------------------------------------------------------

    def _time_window(self) -> tuple[datetime, datetime]:
        """Return the (start, end) of the full plotting window.

        Prefers the span covered by the fine-grained forecast (hourly +
        three-hourly), then the daily-day window, then a one-day window
        starting at "now" (e.g. tests using daily data only, or none).
        """
        return (
            self._window_from_fine_data()
            or self._window_from_days()
            or self._fallback_window()
        )

    def _window_from_fine_data(self) -> tuple[datetime, datetime] | None:
        """The window spanned by the hourly + three-hourly points, or None."""
        start: datetime | None = None
        end: datetime | None = None
        for points in (self._hourly, self._three_hourly):
            for point in points:
                if start is None or point.time < start:
                    start = point.time
                if end is None or point.time > end:
                    end = point.time
        if start is not None and end is not None and end > start:
            return start, end
        return None

    def _window_from_days(self) -> tuple[datetime, datetime] | None:
        """The window spanned by the first-to-last daily points, or None."""
        if not self._days:
            return None
        first = self._days[0].date
        last = self._days[-1].date
        if last > first:
            return first, last
        return None

    def _fallback_window(self) -> tuple[datetime, datetime]:
        """A one-day window starting now (used when no forecast data exists)."""
        now = datetime.now()
        return now, now + timedelta(days=1)

    def _x_for_time(
        self, t: datetime, start: datetime, end: datetime, width: int
    ) -> float:
        """Map a time to a pixel x within the lane, insetting from the Y-axis."""
        span = (end - start).total_seconds()
        if span <= 0:
            return (
                _LEFT_MARGIN
                + _DATA_LEFT_INSET
                + (width - _LEFT_MARGIN - _RIGHT_MARGIN) / 2
            )
        chart_width = width - _LEFT_MARGIN - _RIGHT_MARGIN
        ratio = (t - start).total_seconds() / span
        return _LEFT_MARGIN + _DATA_LEFT_INSET + ratio * chart_width

    # ------------------------------------------------------------------
    # Shared drawing helpers
    # ------------------------------------------------------------------

    def _draw_lane(
        self,
        painter: QPainter,
        width: int,
        height: int,
        series: list[tuple[list[tuple[datetime, float | None]], str]],
        v_min: float,
        v_max: float,
        unit: str,
        icons: list[tuple[str, str]] | None = None,
    ) -> None:
        """Paint one lane: grid + axis labels, lane icons, and one line per series."""
        if not any(pts for pts, _ in series):
            self._draw_lane_icons(painter, width, height, icons)
            painter.setPen(QPen(QColor(_TEXT_COLOR), 1))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(
                QRectF(0, 0, width, height),
                Qt.AlignmentFlag.AlignCenter,
                "No data available",
            )
            return

        window_start, window_end = self._time_window()
        self._draw_lane_frame(painter, width, height, v_min, v_max, unit, icons)
        self._draw_lane_series(
            painter, width, height, v_min, v_max, unit, window_start, window_end, series
        )

    def _draw_lane_frame(
        self,
        painter: QPainter,
        width: int,
        height: int,
        v_min: float,
        v_max: float,
        unit: str,
        icons: list[tuple[str, str]] | None,
    ) -> None:
        """Paint the lane's static chrome: icons, grid lines, Y labels, guides, axis."""
        window_start, window_end = self._time_window()
        plot_top = _TOP_PADDING
        plot_bottom = height - _BOTTOM_PADDING
        plot_height = plot_bottom - plot_top

        self._draw_lane_icons(painter, width, height, icons)

        painter.setFont(QFont("Arial", 9))
        for val, is_zero in self._lane_grid_items(v_min, v_max, unit):
            if v_max == v_min:
                y: float = plot_bottom
            else:
                ratio = (val - v_min) / (v_max - v_min)
                y = plot_bottom - (plot_height * ratio)
            painter.setPen(
                QPen(QColor(_GRID_COLOR_STRONG), 2)
                if is_zero
                else QPen(QColor(_GRID_COLOR), 1)
            )
            painter.drawLine(int(_LEFT_MARGIN), int(y), int(width - _RIGHT_MARGIN), int(y))
            self._draw_lane_axis_label(painter, val, unit, y)

        # Vertical reference lines (midnights + now), under the data series.
        self._draw_vertical_guides(
            painter, window_start, window_end, width, plot_top, plot_bottom
        )

        # Bottom axis.
        painter.setPen(QPen(QColor(_AXIS_COLOR), 1))
        painter.drawLine(int(_LEFT_MARGIN), int(plot_bottom), int(width - _RIGHT_MARGIN), int(plot_bottom))

    def _lane_grid_items(
        self, v_min: float, v_max: float, unit: str
    ) -> list[tuple[float, bool]]:
        """The (value, is_zero) grid-line positions for a lane's Y range.

        Temperature lanes (Celsius): one line at every 5°C within the range,
        with the 0°C line flagged so it can be drawn bolder as a reference.
        Other lanes: three lines at min / mid / max of the range.
        """
        if unit == _TEMP_UNIT:
            grid_vals = list(
                range(
                    math.floor(v_min / 5) * 5,
                    math.ceil(v_max / 5) * 5 + 1,
                    5,
                )
            )
            return [(float(val), val == 0) for val in grid_vals]
        return [(v_min, False), (v_min + (v_max - v_min) / 2, False), (v_max, False)]

    def _draw_lane_axis_label(
        self, painter: QPainter, val: float, unit: str, y: float
    ) -> None:
        """Paint a single Y-axis value label (right-aligned in the left margin)."""
        if unit == _TEMP_UNIT:
            label = f"{val:.0f}\u00b0C"
        elif unit == "%":
            label = f"{val:.0f}%"
        else:
            label = f"{val:.0f}"
        painter.setPen(QPen(QColor(_TEXT_COLOR), 1))
        painter.drawText(
            QRectF(4, y - 8, _LEFT_MARGIN - 8, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            label,
        )

    def _draw_lane_series(
        self,
        painter: QPainter,
        width: int,
        height: int,
        v_min: float,
        v_max: float,
        unit: str,
        window_start: datetime,
        window_end: datetime,
        series: list[tuple[list[tuple[datetime, float | None]], str]],
    ) -> None:
        """Paint each series as a continuous line over the shared time window."""
        plot_top = _TOP_PADDING
        plot_bottom = height - _BOTTOM_PADDING
        plot_height = plot_bottom - plot_top

        def x_pos(t: datetime) -> float:
            return self._x_for_time(t, window_start, window_end, width)

        def y_pos(value: float) -> float:
            if v_max == v_min:
                return plot_bottom
            ratio = (value - v_min) / (v_max - v_min)
            return plot_bottom - (plot_height * ratio)

        for points, color in series:
            self._draw_line(painter, points, color, x_pos, y_pos)

    def _draw_lane_icons(
        self,
        painter: QPainter,
        width: int,
        height: int,
        icons: list[tuple[str, str]] | None,
    ) -> None:
        """Paint lane icons stacked in the left margin (shared by all lanes)."""
        if not icons:
            return
        icon_total = _ICON_SIZE + _ICON_BORDER * 2
        icon_x = 4
        if len(icons) == 1:
            y_offsets = [height / 2]
        else:
            y_offsets = [height * (i + 1) / (len(icons) + 1) for i in range(len(icons))]

        for (icon_key, border_color), cy in zip(icons, y_offsets, strict=True):
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
                target_size,
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            draw_x = icon_x + _ICON_BORDER + (target_size - scaled.width()) // 2
            draw_y = y + _ICON_BORDER + (target_size - scaled.height()) // 2
            painter.drawPixmap(
                QRect(draw_x, draw_y, scaled.width(), scaled.height()), scaled
            )

    def _draw_vertical_guides(
        self,
        painter: QPainter,
        window_start: datetime,
        window_end: datetime,
        width: int,
        top: int,
        bottom: int,
    ) -> None:
        """Draw faint midnight gridlines and a distinct 'now' marker for a lane.

        Midnights are computed in local (UK) time so each line lines up with the
        date-boundary labels under the chart. The 'now' line is drawn only when
        it falls within the window. Called after the horizontal grid but before
        the data series so the lines sit on top of the grid yet under the data.
        """
        left = _LEFT_MARGIN
        right = width - _RIGHT_MARGIN
        if right <= left:
            return

        now = datetime.now(ZoneInfo("UTC"))
        # Match the window's tz awareness so all comparisons are valid.
        if window_start.tzinfo is None:
            now = now.replace(tzinfo=None)

        # Faint midnight gridlines.
        midnight = (window_start + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        while midnight <= window_end:
            x = self._x_for_time(midnight, window_start, window_end, width)
            if left <= x <= right:
                painter.setPen(QPen(QColor(_MIDNIGHT_COLOR), 1))
                painter.drawLine(int(x), int(top), int(x), int(bottom))
            midnight += timedelta(days=1)

        # 'Now' marker (distinct colour + dashed), only when within the window.
        if window_start <= now <= window_end:
            x = self._x_for_time(now, window_start, window_end, width)
            if left <= x <= right:
                pen = QPen(QColor(_NOW_COLOR), 1)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(int(x), int(top), int(x), int(bottom))

    @staticmethod
    def _draw_line(
        painter: QPainter,
        points: list[tuple[datetime, float | None]],
        color: str,
        x_pos: Callable[[datetime], float],
        y_pos: Callable[[float], float],
    ) -> None:
        """Draws a series line (segments + optional sparse dots) for `points`."""
        pts: list[tuple[float, float]] = []
        for t, val in points:
            if val is not None:
                pts.append((x_pos(t), y_pos(float(val))))

        if not pts:
            return

        WeatherGraphWidget._draw_line_segments(painter, pts, color)

        # With many points (dense hourly data) the per-point dots get crowded,
        # so only draw them when the series is sparse enough.
        if len(pts) <= 24:
            WeatherGraphWidget._draw_line_dots(painter, pts, color)

    @staticmethod
    def _draw_line_segments(
        painter: QPainter, pts: list[tuple[float, float]], color: str
    ) -> None:
        """Draws connecting line segments between consecutive plotted points."""
        if len(pts) < 2:
            return
        painter.setPen(QPen(QColor(color), 2))
        for i in range(len(pts) - 1):
            painter.drawLine(
                int(pts[i][0]),
                int(pts[i][1]),
                int(pts[i + 1][0]),
                int(pts[i + 1][1]),
            )

    @staticmethod
    def _draw_line_dots(
        painter: QPainter, pts: list[tuple[float, float]], color: str
    ) -> None:
        """Draws a small dot at each plotted point (used for sparse series)."""
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(QPen(QColor(color), 1))
        for px, py in pts:
            painter.drawEllipse(int(px) - 3, int(py) - 3, 6, 6)

    # ------------------------------------------------------------------
    # Per-lane paint callbacks (called by _LaneFrame.paintEvent)
    # ------------------------------------------------------------------

    def _paint_temp_lane(self, painter: QPainter, width: int, height: int) -> None:
        if self._hourly or self._three_hourly:
            self._paint_temp_lane_data(
                painter, width, height, self._hourly, self._three_hourly
            )
        else:
            self._paint_temp_lane_data(
                painter, width, height, None, None
            )

    def _paint_temp_lane_data(
        self,
        painter: QPainter,
        width: int,
        height: int,
        hourly: list[HourlyForecastPoint] | None,
        three_hourly: list[ThreeHourlyForecastPoint] | None,
    ) -> None:
        if hourly or three_hourly:
            hourly = hourly or []
            three_hourly = three_hourly or []
            min_series = self._continuous_series(
                hourly,
                three_hourly,
                lambda h: (
                    float(h.min_screen_temperature_c)
                    if h.min_screen_temperature_c is not None
                    else None
                ),
                lambda t: (
                    float(t.min_screen_temperature_c)
                    if t.min_screen_temperature_c is not None
                    else None
                ),
            )
            max_series = self._continuous_series(
                hourly,
                three_hourly,
                lambda h: (
                    float(h.max_screen_temperature_c)
                    if h.max_screen_temperature_c is not None
                    else None
                ),
                lambda t: (
                    float(t.max_screen_temperature_c)
                    if t.max_screen_temperature_c is not None
                    else None
                ),
            )
            feels_series = self._continuous_series(
                hourly,
                three_hourly,
                lambda h: (
                    float(h.feels_like_temperature_c)
                    if h.feels_like_temperature_c is not None
                    else None
                ),
                lambda t: (
                    float(t.feels_like_temperature_c)
                    if t.feels_like_temperature_c is not None
                    else None
                ),
            )
            all_vals = self._collect_values([min_series, max_series, feels_series])
            v_min, v_max = self._range_from_values(all_vals, pad=1.0)
            icons = [
                ("temp_high", _TEMP_MAX_COLOR),
                ("temp_feel", _FEELS_LIKE_COLOR),
                ("temp_low", _TEMP_MIN_COLOR),
            ]
            self._draw_lane(
                painter,
                width,
                height,
                [
                    (min_series, _TEMP_MIN_COLOR),
                    (max_series, _TEMP_MAX_COLOR),
                    (feels_series, _FEELS_LIKE_COLOR),
                ],
                v_min,
                v_max,
                unit=_TEMP_UNIT,
                icons=icons,
            )
        else:
            # Defensive fallback: daily data only (e.g. tests without fine data).
            series = [
                (
                    self._daily_series(self._days, lambda d: d.min_temperature_c),
                    _TEMP_MIN_COLOR,
                ),
                (
                    self._daily_series(self._days, lambda d: d.max_temperature_c),
                    _TEMP_MAX_COLOR,
                ),
                (
                    self._daily_series(self._days, lambda d: d.max_feels_like_c),
                    _FEELS_LIKE_COLOR,
                ),
            ]
            all_vals = self._collect_values([s for s, _ in series])
            v_min, v_max = self._range_from_values(all_vals, pad=1.0)
            icons = [
                ("temp_high", _TEMP_MAX_COLOR),
                ("temp_feel", _FEELS_LIKE_COLOR),
                ("temp_low", _TEMP_MIN_COLOR),
            ]
            self._draw_lane(
                painter, width, height, series, v_min, v_max, unit=_TEMP_UNIT, icons=icons
            )

    def _paint_wind_lane(self, painter: QPainter, width: int, height: int) -> None:
        if self._hourly or self._three_hourly:
            self._paint_wind_lane_data(
                painter, width, height, self._hourly, self._three_hourly
            )
        else:
            self._paint_wind_lane_data(
                painter, width, height, None, None
            )

    def _paint_wind_lane_data(
        self,
        painter: QPainter,
        width: int,
        height: int,
        hourly: list[HourlyForecastPoint] | None,
        three_hourly: list[ThreeHourlyForecastPoint] | None,
    ) -> None:
        if hourly or three_hourly:
            hourly = hourly or []
            three_hourly = three_hourly or []
            avg_series = self._continuous_series(
                hourly,
                three_hourly,
                lambda h: (
                    float(h.wind_speed_10m_mph)
                    if h.wind_speed_10m_mph is not None
                    else None
                ),
                lambda t: (
                    float(t.wind_speed_10m_mph)
                    if t.wind_speed_10m_mph is not None
                    else None
                ),
            )
            gust_series = self._continuous_series(
                hourly,
                three_hourly,
                lambda h: (
                    float(h.wind_gust_10m_mph)
                    if h.wind_gust_10m_mph is not None
                    else None
                ),
                lambda t: (
                    float(t.wind_gust_10m_mph)
                    if t.wind_gust_10m_mph is not None
                    else None
                ),
            )
            all_vals = self._collect_values([avg_series, gust_series])
            v_max = (max(all_vals, default=20.0) + 5.0) if all_vals else 25.0
            icons = [("wind", _WIND_COLOR), ("wind", _WIND_GUST_COLOR)]
            self._draw_lane(
                painter,
                width,
                height,
                [(avg_series, _WIND_COLOR), (gust_series, _WIND_GUST_COLOR)],
                0.0,
                v_max,
                unit="mph",
                icons=icons,
            )
        else:
            series = [
                (
                    self._daily_series(self._days, lambda d: d.wind_speed_midday_mph),
                    _WIND_COLOR,
                )
            ]
            all_vals = self._collect_values([series[0][0]])
            v_max = (max(all_vals, default=20.0) + 5.0) if all_vals else 25.0
            icons = [("wind", _WIND_COLOR)]
            self._draw_lane(
                painter, width, height, series, 0.0, v_max, unit="mph", icons=icons
            )

    def _paint_rain_uv_lane(self, painter: QPainter, width: int, height: int) -> None:
        if self._hourly or self._three_hourly:
            self._paint_rain_uv_lane_data(
                painter, width, height, self._hourly, self._three_hourly
            )
        else:
            self._paint_rain_uv_lane_data(
                painter, width, height, None, None
            )

    def _paint_rain_uv_lane_data(
        self,
        painter: QPainter,
        width: int,
        height: int,
        hourly: list[HourlyForecastPoint] | None,
        three_hourly: list[ThreeHourlyForecastPoint] | None,
    ) -> None:
        if hourly or three_hourly:
            hourly = hourly or []
            three_hourly = three_hourly or []
            rain_series = self._continuous_series(
                hourly,
                three_hourly,
                lambda h: (
                    float(h.prob_of_precipitation_pct)
                    if h.prob_of_precipitation_pct is not None
                    else None
                ),
                lambda t: (
                    float(t.prob_of_precipitation_pct)
                    if t.prob_of_precipitation_pct is not None
                    else None
                ),
            )
            uv_series = self._continuous_series(
                hourly,
                three_hourly,
                lambda h: float(h.uv_index) if h.uv_index is not None else None,
                lambda t: float(t.uv_index) if t.uv_index is not None else None,
            )
        else:
            # Defensive fallback: daily data only.
            rain_series = self._daily_series(
                self._days, lambda d: d.rain_probability_pct
            )
            uv_series = self._daily_series(self._days, lambda d: d.uv_index_max)

        icons = [("rain_pct", _RAIN_COLOR), ("uv_index", _UV_COLOR)]
        self._draw_dual_axis_lane(painter, width, height, rain_series, uv_series, icons)

    # ------------------------------------------------------------------
    # Dual-axis lane (rain % on the left axis, UV index on the right axis)
    # ------------------------------------------------------------------

    def _draw_dual_axis_lane(
        self,
        painter: QPainter,
        width: int,
        height: int,
        left_series: list[tuple[datetime, float | None]],
        right_series: list[tuple[datetime, float | None]],
        icons: list[tuple[str, str]] | None,
    ) -> None:
        left_max = 100.0  # rain probability 0-100
        right_max = 11.0  # WHO UV index scale 0-11

        if not (left_series or right_series):
            self._draw_lane_icons(painter, width, height, icons)
            painter.setPen(QPen(QColor(_TEXT_COLOR), 1))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(
                QRectF(0, 0, width, height),
                Qt.AlignmentFlag.AlignCenter,
                "No data available",
            )
            return

        window_start, window_end = self._time_window()

        self._draw_lane_icons(painter, width, height, icons)

        chart_left = _LEFT_MARGIN
        chart_right = width - _RIGHT_MARGIN
        plot_top = _TOP_PADDING
        plot_bottom = height - _BOTTOM_PADDING
        plot_height = plot_bottom - plot_top

        # Grid lines
        painter.setFont(QFont("Arial", 9))
        for i in range(3):
            ratio = i / 2
            y = plot_bottom - (plot_height * ratio)
            painter.setPen(QPen(QColor(_GRID_COLOR), 1))
            painter.drawLine(int(chart_left), int(y), int(chart_right), int(y))

        # Left axis labels (rain %)
        painter.setPen(QPen(QColor(_RAIN_COLOR), 1))
        for i in range(3):
            ratio = i / 2
            y = plot_bottom - (plot_height * ratio)
            val = left_max * ratio
            label = f"{val:.0f}%"
            label_rect = QRectF(4, y - 8, _LEFT_MARGIN - 8, 16)
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label,
            )

        # Right axis labels (UV index), in the right margin
        painter.setPen(QPen(QColor(_UV_COLOR), 1))
        for i in range(3):
            ratio = i / 2
            y = plot_bottom - (plot_height * ratio)
            val = right_max * ratio
            label = f"{val:.0f}"
            label_rect = QRectF(chart_right, y - 8, _RIGHT_MARGIN + 8, 16)
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                label,
            )

        # Vertical reference lines (midnights + now), under the data series
        self._draw_vertical_guides(
            painter, window_start, window_end, width, plot_top, plot_bottom
        )

        # Bottom axis
        painter.setPen(QPen(QColor(_AXIS_COLOR), 1))
        painter.drawLine(
            int(chart_left), int(plot_bottom), int(chart_right), int(plot_bottom)
        )

        def x_pos(t: datetime) -> float:
            return self._x_for_time(t, window_start, window_end, width)

        def y_left(value: float) -> float:
            if left_max == 0:
                return plot_bottom
            return plot_bottom - (plot_height * (value / left_max))

        def y_right(value: float) -> float:
            if right_max == 0:
                return plot_bottom
            return plot_bottom - (plot_height * (value / right_max))

        self._draw_line(painter, left_series, _RAIN_COLOR, x_pos, y_left)
        self._draw_line(painter, right_series, _UV_COLOR, x_pos, y_right)

    # ------------------------------------------------------------------
    # Small numeric helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_values(
        series_list: list[list[tuple[datetime, float | None]]],
    ) -> list[float]:
        vals: list[float] = []
        for series in series_list:
            for _, v in series:
                if v is not None:
                    vals.append(v)
        return vals

    @staticmethod
    def _range_from_values(vals: list[float], pad: float = 0.0) -> tuple[float, float]:
        if not vals:
            return 0.0, 1.0
        v_min = min(vals) - pad
        v_max = max(vals) + pad
        if v_max == v_min:
            v_max = v_min + 1.0
        return v_min, v_max

    @staticmethod
    def _daily_series(
        days: list[DailyForecastPoint],
        getter: Callable[[DailyForecastPoint], Decimal | float | None],
    ) -> list[tuple[datetime, float | None]]:
        """Fallback series built from daily data (used only when no fine data exists)."""
        series: list[tuple[datetime, float | None]] = []
        for d in days:
            val = getter(d)
            series.append((d.date, float(val) if val is not None else None))
        return series

    # ------------------------------------------------------------------
    # Date labels (painted at the bottom of the main widget)
    # ------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._days:
            self._draw_date_labels(painter)

        painter.end()

    def _draw_date_labels(self, painter: QPainter) -> None:
        if not self._days:
            return

        # Position each date label so its centre sits on that day's noon on the
        # shared time axis. Reusing _x_for_time/_time_window means the labels are
        # computed in the same coordinate space as the vertical guide lines, so
        # they line up with the midnight / "now" markers.
        window_start, window_end = self._time_window()

        painter.setPen(QPen(QColor(_TEXT_COLOR), 1))
        painter.setFont(QFont("Arial", 10))

        # Place labels in the 28px bottom strip (below the last lane frame)
        y = self.height() - 22
        for day in self._days:
            # Centre of the date = that day's local noon on the shared time axis.
            noon = day.date.replace(hour=12)
            x = self._x_for_time(noon, window_start, window_end, self.width())
            label = day.date.strftime("%a %d")
            painter.drawText(
                int(x) - 30, y, 60, 16, Qt.AlignmentFlag.AlignCenter, label
            )
