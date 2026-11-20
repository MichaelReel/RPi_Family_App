from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from PyQt6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from config import MET_REFRESH_MS
from lib.metoffice.models import HumanReadableWeatherReport
from lib.metoffice.widgets.four_day_grid import FourDayGridWidget
from lib.metoffice.widgets.location_label import LocationLabelWidget


@pytest.fixture(scope="session", autouse=True)
def q_application() -> QApplication:
    """Ensures a single QApplication instance exists for the test session lifecycle."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        app = QApplication([])
    return app


@pytest.fixture()
def report_source(
    expected_human_report_snapshot: HumanReadableWeatherReport,
) -> Callable[[], HumanReadableWeatherReport]:
    """Provide a source of a test report"""

    def _report_source() -> HumanReadableWeatherReport:
        return expected_human_report_snapshot

    return _report_source


def test_widget_initialization_and_card_count(
    qtbot: QtBot, report_source: Callable[[], HumanReadableWeatherReport]
) -> None:
    """Verifies grid container instantiates exactly 8 interior card objects."""
    grid_widget = FourDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)  # Registers the widget for auto-cleanup

    assert len(grid_widget._cards) == 4


def test_card_data_mapping_and_labels(
    qtbot: QtBot, report_source: Callable[[], HumanReadableWeatherReport]
) -> None:
    """Verifies data properties accurately map to visual text layouts."""
    grid_widget = FourDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)

    first_card = grid_widget._cards[0]

    # First card uses forecast_days[1] (the widget skips index 0):
    # max_temp=18.47, min_temp=5.34, rain=5%, condition=Cloudy
    assert "18.47°C" in first_card._label_temp_high.text()
    assert "5.34°C" in first_card._label_temp_low.text()
    assert first_card._label_cond.text() == "Cloudy"
    assert "5%" in first_card._label_rain.text()


def test_timer_updates_cards_automatically(
    qtbot: QtBot, expected_human_report_snapshot: HumanReadableWeatherReport
) -> None:
    """Verifies that the grid automatically triggers updates when the timer fires."""

    # 1. Create a mock function that we can track
    mock_source = MagicMock(return_value=expected_human_report_snapshot)

    # 2. Instantiate the widget (this runs report_source once on startup)
    grid_widget = FourDayGridWidget(report_source=mock_source)
    qtbot.addWidget(grid_widget)

    # Reset our tracking statistics to clear out the startup call
    mock_source.reset_mock()

    # 3. Simulate an automatic background clock ticking event
    # This fires the .timeout signal instantly, bypassing the real delay
    grid_widget._refresh_timer.timeout.emit()

    # 4. Verify that the update method requested data again
    mock_source.assert_called_once()


def test_timer_configuration_properties(
    qtbot: QtBot, report_source: Callable[[], HumanReadableWeatherReport]
) -> None:
    """Verifies the underlying timer structure runs continuously with correct ms."""
    grid_widget = FourDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)

    # Verify the background configuration is active
    assert grid_widget._refresh_timer.isActive() is True

    # Verify it isn't restricted to a single shot execution loop
    assert grid_widget._refresh_timer.isSingleShot() is False

    # Verify it matches your configuration file settings exactly
    assert grid_widget._refresh_timer.interval() == MET_REFRESH_MS


def test_featured_layout_initialization(
    qtbot: QtBot, report_source: Callable[[], HumanReadableWeatherReport]
) -> None:
    """Verifies all 4 weather cards map correctly into their primary layout hierarchies."""
    grid_widget = FourDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)

    # 1. Verify card array tracking matches limits
    assert len(grid_widget._cards) == 4

    # 2. Verify layout distributions structurally match expectations
    assert grid_widget._main_layout.count() == 2  # Feature card + secondary layout track
    assert (
        grid_widget._secondary_layout.count() == 3
    )  # Contains remaining cards 2, 3, and 4


def test_setup_grid_data_handles_report_source_exception(
    qtbot: QtBot, expected_human_report_snapshot: HumanReadableWeatherReport
) -> None:
    """If report_source raises an exception during setup, the widget should raise RuntimeError."""

    def failing_source() -> HumanReadableWeatherReport:
        raise RuntimeError("API failure")

    with pytest.raises(RuntimeError, match="met office API issues"):
        FourDayGridWidget(report_source=failing_source)


def test_update_grid_data_handles_report_source_exception(
    qtbot: QtBot,
    expected_human_report_snapshot: HumanReadableWeatherReport,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If report_source raises during a timer-triggered update, the error should be logged, not crash."""
    grid_widget = FourDayGridWidget(
        report_source=lambda: expected_human_report_snapshot
    )
    qtbot.addWidget(grid_widget)

    # Replace with a failing source after setup
    grid_widget.report_source = lambda: (_ for _ in ()).throw(
        RuntimeError("API failure")
    )

    with caplog.at_level("ERROR"):
        grid_widget.update_grid_data()

    assert "Error calling report_source" in caplog.text
    assert "API failure" in caplog.text


def test_location_label_shows_name(
    qtbot: QtBot, expected_human_report_snapshot: HumanReadableWeatherReport
) -> None:
    """Widget should display the location name when it is present."""
    widget = LocationLabelWidget(location_name="Falmouth")
    qtbot.addWidget(widget)
    widget.show()

    assert widget._label.text() == "Falmouth"
    assert widget._label.isVisible() is True


def test_location_label_hidden_when_none(qtbot: QtBot) -> None:
    """Widget should hide its label when location_name is None and no coordinates."""
    widget = LocationLabelWidget(location_name=None, coordinates=None)
    qtbot.addWidget(widget)
    widget.show()

    assert widget._label.isVisible() is False


def test_location_label_hidden_when_empty(qtbot: QtBot) -> None:
    """Widget should hide its label when location_name is empty and no coordinates."""
    widget = LocationLabelWidget(location_name="", coordinates=None)
    qtbot.addWidget(widget)
    widget.show()

    assert widget._label.isVisible() is False


def test_location_label_shows_coordinates_when_no_name(qtbot: QtBot) -> None:
    """Widget should display coordinates as fallback when location_name is blank."""
    from decimal import Decimal

    widget = LocationLabelWidget(
        location_name=None,
        coordinates=[Decimal("-7.4058"), Decimal("54.3141"), Decimal("74.0")],
    )
    qtbot.addWidget(widget)
    widget.show()

    assert widget._label.text() == "54.3141, -7.4058"
    assert widget._label.isVisible() is True
