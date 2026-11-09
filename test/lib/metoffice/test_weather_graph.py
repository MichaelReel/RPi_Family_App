"""Tests for the WeatherGraphWidget."""
from datetime import datetime, timedelta
from decimal import Decimal

from lib.metoffice.models import DailyForecastPoint, HumanReadableWeatherReport
from lib.metoffice.widgets.weather_graph import WeatherGraphWidget


def _make_days(count: int = 7) -> list[DailyForecastPoint]:
    """Generate a list of DailyForecastPoint values for testing."""
    base_date = datetime(2026, 11, 10)
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


def _make_report(days: list[DailyForecastPoint]) -> HumanReadableWeatherReport:
    return HumanReadableWeatherReport(
        location_name="Testville",
        coordinates=[Decimal("51.5"), Decimal("-0.1")],
        model_run_at=datetime(2026, 11, 9),
        forecast_days=days,
    )


def test_graph_widget_initialisation(qtbot) -> None:
    """Widget should initialise with data from the report source."""
    report = _make_report(_make_days(8))
    widget = WeatherGraphWidget(report_source=lambda: report)
    qtbot.addWidget(widget)
    widget.show()

    # Should have 7 days (indices 1-7 of the 8-day report)
    assert len(widget._days) == 7
    assert widget._days[0].max_temperature_c == Decimal(16)


def test_graph_widget_handles_none_report(qtbot) -> None:
    """Widget should handle a report source that returns None."""
    widget = WeatherGraphWidget(report_source=lambda: None)
    qtbot.addWidget(widget)
    widget.show()

    assert len(widget._days) == 0


def test_graph_widget_handles_exception(qtbot) -> None:
    """Widget should handle a report source that raises."""
    def bad_source() -> None:
        raise RuntimeError("boom")

    widget = WeatherGraphWidget(report_source=bad_source)
    qtbot.addWidget(widget)
    widget.show()

    assert len(widget._days) == 0


def test_graph_widget_background_color(qtbot) -> None:
    """Widget should apply the background colour from its stylesheet."""
    widget = WeatherGraphWidget(report_source=lambda: _make_report(_make_days(8)))
    qtbot.addWidget(widget)
    widget.show()

    style = widget.styleSheet()
    assert "#000022" in style


def test_graph_widget_takes_next_seven_days(qtbot) -> None:
    """Widget should use forecast_days[1:8] — the next 7 days, skipping today."""
    days = _make_days(10)  # 10 days total
    report = _make_report(days)
    widget = WeatherGraphWidget(report_source=lambda: report)
    qtbot.addWidget(widget)
    widget.show()

    assert len(widget._days) == 7
    assert widget._days[0] == days[1]
    assert widget._days[-1] == days[7]
