"""Tests for the WeatherGraphWidget."""

from datetime import datetime, timedelta
from decimal import Decimal

from freezegun import freeze_time
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from pytestqt.qtbot import QtBot

from lib.metoffice.models import (
    DailyForecastPoint,
    HourlyForecastPoint,
    HumanReadableWeatherReport,
    ThreeHourlyForecastPoint,
)
from lib.metoffice.widgets.weather_graph import WeatherGraphWidget


def _make_days(count: int = 7) -> list[DailyForecastPoint]:
    """Generate a list of DailyForecastPoint values for testing."""
    base_date = datetime(2026, 11, 25)
    days: list[DailyForecastPoint] = []
    for i in range(count):
        days.append(
            DailyForecastPoint(
                date=base_date + timedelta(days=i),
                max_temperature_c=Decimal(15 + i),
                min_temperature_c=Decimal(5 + i),
                max_feels_like_c=Decimal(14 + i),
                rain_probability_pct=10 * i,
                snow_probability_pct=None,
                wind_speed_midday_mph=Decimal(5 + i * 2),
                wind_direction_midday_deg=180,
                visibility_midday_metres=5000,
                uv_index_max=5,
                weather_code=1,
                weather_condition="Sunny day",
            )
        )
    return days


def _make_report(
    days: list[DailyForecastPoint],
    hourly: list[HourlyForecastPoint] | None = None,
    three_hourly: list[ThreeHourlyForecastPoint] | None = None,
) -> HumanReadableWeatherReport:
    return HumanReadableWeatherReport(
        location_name="Testville",
        coordinates=[Decimal("51.5"), Decimal("-0.1")],
        model_run_at=datetime(2026, 11, 9),
        forecast_days=days,
        forecast_hourly=hourly or [],
        forecast_three_hourly=three_hourly or [],
    )


def test_graph_widget_initialisation(qtbot: QtBot) -> None:
    """Widget should initialise with data from the report source."""
    report = _make_report(_make_days(8))
    widget = WeatherGraphWidget(report_source=lambda: report)
    qtbot.addWidget(widget)
    widget.show()

    # 8-day report: the slice forecast_days[1:9] yields indices 1-7 (7 days).
    assert len(widget._days) == 7
    assert widget._days[0].max_temperature_c == Decimal(16)


def test_graph_widget_handles_none_report(qtbot: QtBot) -> None:
    """Widget should handle a report source that returns None."""
    widget = WeatherGraphWidget(report_source=lambda: None)
    qtbot.addWidget(widget)
    widget.show()

    assert len(widget._days) == 0


def test_graph_widget_handles_exception(qtbot: QtBot) -> None:
    """Widget should handle a report source that raises."""

    def bad_source() -> None:
        raise RuntimeError("boom")

    widget = WeatherGraphWidget(report_source=bad_source)
    qtbot.addWidget(widget)
    widget.show()

    assert len(widget._days) == 0


def test_graph_widget_background_color(qtbot: QtBot) -> None:
    """Widget should apply the background colour from its stylesheet."""
    widget = WeatherGraphWidget(report_source=lambda: _make_report(_make_days(8)))
    qtbot.addWidget(widget)
    widget.show()

    style = widget.styleSheet()
    assert "#000022" in style


def test_graph_widget_takes_next_seven_days(qtbot: QtBot) -> None:
    """Widget should use forecast_days[1:8] — the next 7 days, skipping today."""
    days = _make_days(10)  # 10 days total
    report = _make_report(days)
    widget = WeatherGraphWidget(report_source=lambda: report)
    qtbot.addWidget(widget)
    widget.show()

    assert len(widget._days) == 7
    assert widget._days[0] == days[1]
    assert widget._days[-1] == days[7]


def test_eighth_day_label_derived_from_fine_data(qtbot: QtBot) -> None:
    """The 8th day's date label must be derived from the fine-data window.

    The daily API only returns today + 7 days, but the 3-hourly series runs ~8
    days out. When the plotted fine-data window extends a full extra day beyond
    the last daily label, the widget must append a synthetic label for that day
    so the X-axis covers every day that is mostly displayed.
    """
    from datetime import timedelta

    days = _make_days(8)  # 8 daily days: today + 7
    # 3-hourly data extends ~8 days beyond the first daily date, so the last
    # daily date is ~1 day behind the fine-data end.
    base = days[0].date
    three_hourly = [
        ThreeHourlyForecastPoint(
            time=base + timedelta(hours=24 * i),
            screen_temperature_c=Decimal(10),
            min_screen_temperature_c=Decimal(5),
            max_screen_temperature_c=Decimal(15),
            feels_like_temperature_c=Decimal(10),
            wind_speed_10m_mph=Decimal(5),
            wind_gust_10m_mph=Decimal(10),
            wind_direction_10m_deg=180,
            relative_humidity_pct=Decimal(80),
            precipitation_rate_mmh=Decimal(0),
            total_precip_amount_mm=Decimal(0),
            prob_of_precipitation_pct=20,
            uv_index=1,
            significant_weather_code=3,
        )
        for i in range(0, 24 * 8, 6)  # every 6h for 8 days
    ]
    report = _make_report(days, three_hourly=three_hourly)
    widget = WeatherGraphWidget(report_source=lambda: report)
    qtbot.addWidget(widget)
    widget.show()

    # 7 from the daily slice + 1 derived = 8 total labels.
    assert len(widget._days) == 8
    assert widget._days[0] == days[1]
    assert widget._days[7].date == days[7].date + timedelta(days=1)
    # The synthetic label carries no stats (date only).
    assert widget._days[7].max_temperature_c is None
    assert widget._days[7].weather_condition == ""


# ------------------------------------------------------------------
# Fine-data (hourly + three-hourly) series construction and lanes
# ------------------------------------------------------------------


def _make_hourly(
    points: list[tuple[int, float, float, float, float]],
) -> list[HourlyForecastPoint]:
    """Build hourly points. Each item is (hour_offset, screen, min, max, feels)."""
    base = datetime(2026, 11, 25)
    out: list[HourlyForecastPoint] = []
    for offset, temp, mn, mx, feels in points:
        out.append(
            HourlyForecastPoint(
                time=base + timedelta(hours=offset),
                screen_temperature_c=Decimal(temp),
                min_screen_temperature_c=Decimal(mn),
                max_screen_temperature_c=Decimal(mx),
                feels_like_temperature_c=Decimal(feels),
                wind_speed_10m_mph=Decimal(5),
                wind_gust_10m_mph=Decimal(10),
                wind_direction_10m_deg=180,
                relative_humidity_pct=Decimal(80),
                precipitation_rate_mmh=Decimal(0),
                total_precip_amount_mm=Decimal(0),
                prob_of_precipitation_pct=20,
                uv_index=1,
                significant_weather_code=3,
            )
        )
    return out


def _make_three_hourly(
    points: list[tuple[int, float, float, float]],
) -> list[ThreeHourlyForecastPoint]:
    """Build 3-hourly points. Each item is (hour_offset, min_temp, max_temp, feels)."""
    base = datetime(2026, 11, 25)
    out: list[ThreeHourlyForecastPoint] = []
    for offset, mn, mx, feels in points:
        out.append(
            ThreeHourlyForecastPoint(
                time=base + timedelta(hours=offset),
                screen_temperature_c=Decimal((mn + mx) / 2),
                min_screen_temperature_c=Decimal(mn),
                max_screen_temperature_c=Decimal(mx),
                feels_like_temperature_c=Decimal(feels),
                wind_speed_10m_mph=Decimal(6),
                wind_gust_10m_mph=Decimal(12),
                wind_direction_10m_deg=200,
                relative_humidity_pct=Decimal(85),
                precipitation_rate_mmh=Decimal(0),
                total_precip_amount_mm=Decimal(0),
                prob_of_precipitation_pct=30,
                uv_index=0,
                significant_weather_code=7,
            )
        )
    return out


def test_filter_recent_drops_points_older_than_24h() -> None:
    """Fine-grained points older than 24h before "now" must be dropped.

    Regression: the Met Office forecast starts a few hours in the past, and that
    start time is fixed at fetch time. Without filtering, the graph's left edge
    keeps showing stale historical data as the app runs for days. The filter
    anchors the plotted window to "now" so the start position advances with time.
    """
    with freeze_time("2026-11-25 12:00:00"):
        now = datetime.now()
        old = now - timedelta(hours=30)  # older than 24h -> dropped
        recent = now - timedelta(hours=2)  # within 24h -> kept
        future = now + timedelta(hours=6)  # in the future -> kept

        points = [
            _make_hourly_point(old, 10),
            _make_hourly_point(recent, 11),
            _make_hourly_point(future, 12),
        ]

        filtered = WeatherGraphWidget._filter_recent(points)
        assert [p.time for p in filtered] == [recent, future]
        assert old not in [p.time for p in filtered]


def test_filter_recent_handles_naive_datetimes() -> None:
    """The filter must not raise when points carry naive (tz-less) datetimes."""
    with freeze_time("2026-11-25 12:00:00"):
        now = datetime.now()  # naive
        old = now - timedelta(hours=30)
        recent = now - timedelta(hours=2)

        points = [
            _make_hourly_point(old, 10),
            _make_hourly_point(recent, 11),
        ]

        filtered = WeatherGraphWidget._filter_recent(points)
        assert [p.time for p in filtered] == [recent]


def _make_hourly_point(time: datetime, temp: float) -> HourlyForecastPoint:
    """Build a single HourlyForecastPoint at `time` with a given screen temp."""
    return HourlyForecastPoint(
        time=time,
        screen_temperature_c=Decimal(temp),
        min_screen_temperature_c=Decimal(temp - 4),
        max_screen_temperature_c=Decimal(temp + 2),
        feels_like_temperature_c=Decimal(temp - 2),
        wind_speed_10m_mph=Decimal(5),
        wind_gust_10m_mph=Decimal(10),
        wind_direction_10m_deg=180,
        relative_humidity_pct=Decimal(80),
        precipitation_rate_mmh=Decimal(0),
        total_precip_amount_mm=Decimal(0),
        prob_of_precipitation_pct=20,
        uv_index=1,
        significant_weather_code=3,
    )


def test_continuous_series_dedupes_shared_timestamps_hourly_wins() -> None:
    """Where hourly and three-hourly share a timestamp, the hourly value is used."""
    base = datetime(2026, 11, 25)
    hourly = [
        HourlyForecastPoint(
            time=base,
            screen_temperature_c=Decimal(10),
            min_screen_temperature_c=Decimal(4),
            max_screen_temperature_c=Decimal(12),
            feels_like_temperature_c=Decimal(8),
            wind_speed_10m_mph=Decimal(5),
            wind_gust_10m_mph=Decimal(10),
            wind_direction_10m_deg=180,
            relative_humidity_pct=Decimal(80),
            precipitation_rate_mmh=Decimal(0),
            total_precip_amount_mm=Decimal(0),
            prob_of_precipitation_pct=20,
            uv_index=1,
            significant_weather_code=3,
        )
    ]
    three_hourly = [
        ThreeHourlyForecastPoint(
            time=base,  # shared timestamp -> must be dropped (hourly wins)
            screen_temperature_c=Decimal(99),
            min_screen_temperature_c=Decimal(1),
            max_screen_temperature_c=Decimal(99),
            feels_like_temperature_c=Decimal(99),
            wind_speed_10m_mph=Decimal(6),
            wind_gust_10m_mph=Decimal(12),
            wind_direction_10m_deg=200,
            relative_humidity_pct=Decimal(85),
            precipitation_rate_mmh=Decimal(0),
            total_precip_amount_mm=Decimal(0),
            prob_of_precipitation_pct=30,
            uv_index=0,
            significant_weather_code=7,
        ),
        ThreeHourlyForecastPoint(
            time=base + timedelta(hours=3),  # distinct timestamp -> kept
            screen_temperature_c=Decimal(7),
            min_screen_temperature_c=Decimal(5),
            max_screen_temperature_c=Decimal(12),
            feels_like_temperature_c=Decimal(6),
            wind_speed_10m_mph=Decimal(6),
            wind_gust_10m_mph=Decimal(12),
            wind_direction_10m_deg=200,
            relative_humidity_pct=Decimal(85),
            precipitation_rate_mmh=Decimal(0),
            total_precip_amount_mm=Decimal(0),
            prob_of_precipitation_pct=30,
            uv_index=0,
            significant_weather_code=7,
        ),
    ]

    series = WeatherGraphWidget._continuous_series(
        hourly,
        three_hourly,
        lambda h: (
            float(h.screen_temperature_c)
            if h.screen_temperature_c is not None
            else None
        ),
        lambda t: (
            float(t.max_screen_temperature_c)
            if t.max_screen_temperature_c is not None
            else None
        ),
    )

    by_time = dict(series)
    assert by_time[base] == 10.0  # hourly screen temp, not the 3-hourly max
    assert by_time[base + timedelta(hours=3)] == 12.0  # distinct 3-hourly max kept
    assert len(series) == 2


def test_temp_min_max_lines_are_continuous_from_hourly() -> None:
    """Min/max lines must use hourly min/max in the first 48h, not go blank.

    Regression: the 3-hourly series only starts ~day 3, so min/max built from
    3-hourly alone left the first 48h blank. The hourly API also exposes
    minScreenAirTemp/maxScreenAirTemp, which must fill that span.
    """
    base = datetime(2026, 11, 25)
    hourly = _make_hourly([(0, 8, 6, 11, 5), (1, 7, 5, 10, 4), (2, 6, 4, 9, 3)])
    three_hourly = _make_three_hourly([(3, 5, 12, 6), (6, 4, 13, 5)])

    min_series = WeatherGraphWidget._continuous_series(
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
    max_series = WeatherGraphWidget._continuous_series(
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

    # The first 48h (the 3 hourly points) are populated from the hourly min/max,
    # not dropped as None — this is what removed the old flat/blank stretch.
    assert [t for t, _ in min_series[:3]] == [
        base + timedelta(hours=i) for i in range(3)
    ]
    assert [v for _, v in min_series[:3]] == [6.0, 5.0, 4.0]
    assert [v for _, v in max_series[:3]] == [11.0, 10.0, 9.0]

    # The 3-hourly segment still extends the lines beyond the hourly span.
    assert min_series[-1][1] == 4.0
    assert max_series[-1][1] == 13.0


def test_continuous_series_is_sorted_by_time() -> None:
    """The merged series must be in chronological order regardless of input order."""
    base = datetime(2026, 11, 25)
    hourly = _make_hourly([(24, 11, 7, 15, 9)])  # later than the 3-hourly point below
    three_hourly = _make_three_hourly([(0, 5, 12, 6)])

    series = WeatherGraphWidget._continuous_series(
        hourly,
        three_hourly,
        lambda h: (
            float(h.screen_temperature_c)
            if h.screen_temperature_c is not None
            else None
        ),
        lambda t: (
            float(t.screen_temperature_c)
            if t.screen_temperature_c is not None
            else None
        ),
    )
    assert [t for t, _ in series] == sorted([t for t, _ in series])
    assert series[0][0] == base
    assert series[0][1] == 8.5  # 3-hourly screen temp ((5+12)/2) at the earliest time


def test_widget_with_fine_data_populates_all_series_and_paints(qtbot: QtBot) -> None:
    """With hourly + three-hourly data the widget stores both and paints without error."""
    with freeze_time("2026-11-25 12:00:00"):
        days = _make_days(8)
        hourly = _make_hourly([(0, 10, 6, 12, 8), (1, 11, 7, 13, 9), (2, 12, 8, 14, 10)])
        three_hourly = _make_three_hourly([(3, 5, 12, 6), (6, 4, 13, 5), (24, 6, 15, 7)])
        report = _make_report(days, hourly=hourly, three_hourly=three_hourly)

        widget = WeatherGraphWidget(report_source=lambda: report)
        qtbot.addWidget(widget)
        widget.show()

        assert len(widget._days) == 7
        assert len(widget._hourly) == 3
        assert len(widget._three_hourly) == 3

        # Force a full paint of every lane; must not raise.
        for frame in widget._frames:
            frame.grab()
        widget.grab()


def test_temp_lane_draws_midnight_gridlines(qtbot: QtBot) -> None:
    """The temp lane must paint faint vertical midnight gridlines.

    Renders the lane into a pixmap and checks the midnight guide colour
    (#3A3A5C) appears — i.e. the vertical day-boundary lines are drawn.
    """
    days = _make_days(8)
    hourly = _make_hourly([(0, 10, 6, 12, 8), (1, 11, 7, 13, 9), (2, 12, 8, 14, 10)])
    three_hourly = _make_three_hourly([(3, 5, 12, 6), (6, 4, 13, 5), (24, 6, 15, 7)])
    report = _make_report(days, hourly=hourly, three_hourly=three_hourly)

    widget = WeatherGraphWidget(report_source=lambda: report)
    qtbot.addWidget(widget)
    widget.resize(1200, 600)
    widget.show()

    # Grab the first lane frame (the temperature lane) and inspect its pixels.
    frame = widget._frames[0]
    frame.resize(frame.size())
    pixmap = QPixmap(frame.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    frame.render(pixmap)
    image = pixmap.toImage()

    target = QColor("#3A3A5C")
    tol = 12  # tolerate antialiasing / blending
    hit = 0
    for y in range(image.height()):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            if (
                abs(c.red() - target.red()) <= tol
                and abs(c.green() - target.green()) <= tol
                and abs(c.blue() - target.blue()) <= tol
            ):
                hit += 1
    assert hit > 0, "expected midnight gridline colour to be painted in the temp lane"


def test_temp_lane_zero_c_gridline_is_bold(qtbot: QtBot) -> None:
    """The temp lane must paint a slightly bolder 0°C gridline when the range crosses it.

    Renders the temperature lane into a pixmap and checks the bold grid colour
    (_GRID_COLOR_STRONG) appears alongside the normal grid colour (_GRID_COLOR),
    i.e. horizontal lines are drawn at every 5°C with 0°C drawn bolder.
    """
    from config.ui import GRAPH_GRID_COLOR, GRAPH_GRID_COLOR_STRONG

    with freeze_time("2026-11-25 12:00:00"):
        days = _make_days(8)
        # Range spans -1.0 .. 11.0 so the 0 and 5 multiples both fall in range.
        hourly = _make_hourly([(0, 5, -1, 8, 4), (1, 4, -1, 7, 3), (2, 6, 0, 9, 5)])
        three_hourly = _make_three_hourly([(3, -1, 10, 4), (6, 0, 11, 5)])
        report = _make_report(days, hourly=hourly, three_hourly=three_hourly)

        widget = WeatherGraphWidget(report_source=lambda: report)
        qtbot.addWidget(widget)
        widget.resize(1200, 600)
        widget.show()

        frame = widget._frames[0]
        frame.resize(frame.size())
        pixmap = QPixmap(frame.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        frame.render(pixmap)
        image = pixmap.toImage()

        tol = 12  # tolerate antialiasing / blending

        def count_near(target: QColor) -> int:
            n = 0
            for y in range(image.height()):
                for x in range(image.width()):
                    c = image.pixelColor(x, y)
                    if (
                        abs(c.red() - target.red()) <= tol
                        and abs(c.green() - target.green()) <= tol
                        and abs(c.blue() - target.blue()) <= tol
                    ):
                        n += 1
            return n

        assert count_near(QColor(GRAPH_GRID_COLOR_STRONG)) > 0, (
            "expected the bold 0°C gridline colour to be painted in the temp lane"
        )
        assert count_near(QColor(GRAPH_GRID_COLOR)) > 0, (
            "expected the normal 5°C gridline colour to be painted in the temp lane"
        )


def test_date_labels_are_centred_on_noon(qtbot: QtBot) -> None:
    """Each on-screen date label must be centred on that day's noon on the time axis.

    Renders the parent widget and checks that every painted date-label cluster
    sits on the x position the code computes for that day's noon via
    _x_for_time/_time_window — i.e. the labels sit on the same time-based x as
    the vertical guide lines, not evenly spaced across the lane width.
    """
    from config.ui import GRAPH_TEXT_COLOR

    # Daily dates run base+1d .. base+7d. The fine-data window below spans
    # base .. base+2.1d, so the first two daily labels (base+1d, base+2d) fall
    # inside the window and are expected to render on screen.
    days = _make_days(8)
    hourly = _make_hourly([(i, 10, 6, 12, 8) for i in range(0, 52, 3)])
    report = _make_report(days, hourly=hourly)

    widget = WeatherGraphWidget(report_source=lambda: report)
    qtbot.addWidget(widget)
    widget.resize(1200, 600)
    widget.show()
    widget.grab()  # force a full paint of the parent (incl. the date labels)

    pixmap = QPixmap(widget.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    widget.render(pixmap)
    image = pixmap.toImage()

    target = QColor(GRAPH_TEXT_COLOR)
    tol = 40  # tolerate antialiasing / blending
    label_y = widget.height() - 22
    y_lo, y_hi = max(0, label_y - 10), min(image.height(), label_y + 12)

    xs: list[int] = []
    for y in range(y_lo, y_hi):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            if (
                abs(c.red() - target.red()) <= tol
                and abs(c.green() - target.green()) <= tol
                and abs(c.blue() - target.blue()) <= tol
            ):
                xs.append(x)
    assert xs, "expected date label text to be painted in the bottom strip"

    # Cluster the label pixels into the discrete per-day labels.
    xs.sort()
    clusters: list[list[int]] = [[xs[0]]]
    for x in xs[1:]:
        if x - clusters[-1][-1] > 15:  # gap between adjacent date labels
            clusters.append([x])
        else:
            clusters[-1].append(x)

    window_start, window_end = widget._time_window()
    # Expected x for every daily label that falls inside the window.
    expected = [
        (
            day.date,
            widget._x_for_time(
                day.date.replace(hour=12), window_start, window_end, widget.width()
            ),
        )
        for day in widget._days
        if window_start <= day.date.replace(hour=12) <= window_end
    ]
    assert expected, "expected at least one daily label to fall within the window"

    for label_centre_x, (_, exp_x) in zip(
        (sum(cl) / len(cl) for cl in clusters),
        sorted(expected, key=lambda e: e[1]),
        strict=True,
    ):
        assert abs(label_centre_x - exp_x) < 15, (
            f"date label centred at x={label_centre_x:.1f} does not sit on its "
            f"day's noon x={exp_x:.1f}"
        )
