import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from PySide6.QtWidgets import QApplication
from unittest.mock import MagicMock

from config import MET_REFRESH_MS
from lib.metoffice.models import DailyForecastPoint, HumanReadableWeatherReport
from lib.metoffice.widgets.day_card import DayCardWidget
from lib.metoffice.widgets.eight_day_grid import EightDayGridWidget

from test.test_data.metoffice_sitespecific_point_daily.model import expected_human_report_snapshot


@pytest.fixture(scope="session", autouse=True)
def q_application():
    """Ensures a single QApplication instance exists for the test session lifecycle."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture()
def report_source(
    expected_human_report_snapshot: HumanReadableWeatherReport
) -> callable[[],HumanReadableWeatherReport]:
    """Provide a source of a test report"""
    def _report_source() -> HumanReadableWeatherReport:
        return expected_human_report_snapshot

    return _report_source


def test_widget_initialization_and_card_count(qtbot, report_source):
    """Verifies grid container instantiates exactly 8 interior card objects."""
    grid_widget = EightDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget) # Registers the widget for auto-cleanup
    
    assert len(grid_widget.cards) == 8


def test_card_data_mapping_and_labels(qtbot, report_source):
    """Verifies data properties accurately map to visual text layouts."""
    grid_widget = EightDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)
    
    first_card = grid_widget.cards[0]
    
    assert "High: 18.34°C" in first_card.lbl_temps.text()
    assert "Low: 8.43°C" in first_card.lbl_temps.text()
    assert first_card.lbl_cond.text() == "Cloudy"
    assert first_card.lbl_rain.text() == "🌧️ Rain Chance: 73%"


def test_dynamic_reflow_layout_columns(qtbot, report_source):
    """Verifies screen resize operations force the grid into 4x2 or 2x4 structures."""
    grid_widget = EightDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)
    grid_widget.show()

    # 1. Simulate wide screen format (Landscape)
    grid_widget.resize(800, 300)
    qtbot.waitExposed(grid_widget) # Safely yields loop control to process UI layout updates
    assert grid_widget.current_columns == 4
    
    # 2. Simulate skinny screen format (Portrait)
    grid_widget.resize(300, 800)
    # Wait for the layout to recalculate and stabilize
    qtbot.waitUntil(lambda: grid_widget.current_columns == 2, timeout=1000)
    assert grid_widget.current_columns == 2


def test_timer_updates_cards_automatically(qtbot, expected_human_report_snapshot):
    """Verifies that the grid automatically triggers updates when the timer fires."""
    
    # 1. Create a mock function that we can track
    mock_source = MagicMock(return_value=expected_human_report_snapshot)
    
    # 2. Instantiate the widget (this runs report_source once on startup)
    grid_widget = EightDayGridWidget(report_source=mock_source)
    qtbot.addWidget(grid_widget)
    
    # Reset our tracking statistics to clear out the startup call
    mock_source.reset_mock()
    
    # 3. Simulate an automatic background clock ticking event
    # This fires the .timeout signal instantly, bypassing the real delay
    grid_widget.refresh_timer.timeout.emit()
    
    # 4. Verify that the update method requested data again
    mock_source.assert_called_once()


def test_timer_configuration_properties(qtbot, report_source):
    """Verifies the underlying timer structure runs continuously with correct ms."""
    grid_widget = EightDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)
    
    # Verify the background configuration is active
    assert grid_widget.refresh_timer.isActive() is True
    
    # Verify it isn't restricted to a single shot execution loop
    assert grid_widget.refresh_timer.isSingleShot() is False
    
    # Verify it matches your configuration file settings exactly
    assert grid_widget.refresh_timer.interval() == MET_REFRESH_MS