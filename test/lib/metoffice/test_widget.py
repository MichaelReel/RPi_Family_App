import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import QApplication
from unittest.mock import MagicMock

from config import MET_REFRESH_MS
from lib.metoffice.models import DailyForecastPoint, HumanReadableWeatherReport
from lib.metoffice.widgets.day_card import DayCardWidget
from lib.metoffice.widgets.four_day_grid import FourDayGridWidget, LayoutMode

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
    grid_widget = FourDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget) # Registers the widget for auto-cleanup
    
    assert len(grid_widget.cards) == 4


def test_card_data_mapping_and_labels(qtbot, report_source):
    """Verifies data properties accurately map to visual text layouts."""
    grid_widget = FourDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)
    
    first_card = grid_widget.cards[0]
    
    assert "High: 18.47°C" in first_card.lbl_temps.text()
    assert "Low: 5.34°C" in first_card.lbl_temps.text()
    assert first_card.lbl_cond.text() == "Cloudy"
    assert first_card.lbl_rain.text() == "🌧️ Rain Chance: 5%"


def test_dynamic_reflow_layout_modes_headless(qtbot, report_source) -> None:
    """Verifies layout modes change accurately without rendering a visual window."""
    # Instantiate the widget without calling .show() or adding it to a visible parent
    grid_widget = FourDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)

    # 1. Simulate wide screen format (Horizontal aspect ratio >= 2.0)
    new_size = QSize(800, 300)
    grid_widget.resize(new_size)
    # Explicitly dispatch the resize event to bypass the window manager
    grid_widget.resizeEvent(QResizeEvent(new_size, QSize(0, 0)))
    assert grid_widget.current_layout_mode == LayoutMode.HORIZONTAL
    
    # 2. Simulate standard screen format (Square aspect ratio between 0.5 and 2.0)
    new_size = QSize(500, 500)
    grid_widget.resize(new_size)
    grid_widget.resizeEvent(QResizeEvent(new_size, QSize(800, 300)))
    assert grid_widget.current_layout_mode == LayoutMode.SQUARE

    # 3. Simulate skinny screen format (Vertical aspect ratio <= 0.5)
    new_size = QSize(300, 800)
    grid_widget.resize(new_size)
    grid_widget.resizeEvent(QResizeEvent(new_size, QSize(500, 500)))
    assert grid_widget.current_layout_mode == LayoutMode.VERTICAL


def test_timer_updates_cards_automatically(qtbot, expected_human_report_snapshot):
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
    grid_widget.refresh_timer.timeout.emit()
    
    # 4. Verify that the update method requested data again
    mock_source.assert_called_once()


def test_timer_configuration_properties(qtbot, report_source):
    """Verifies the underlying timer structure runs continuously with correct ms."""
    grid_widget = FourDayGridWidget(report_source=report_source)
    qtbot.addWidget(grid_widget)
    
    # Verify the background configuration is active
    assert grid_widget.refresh_timer.isActive() is True
    
    # Verify it isn't restricted to a single shot execution loop
    assert grid_widget.refresh_timer.isSingleShot() is False
    
    # Verify it matches your configuration file settings exactly
    assert grid_widget.refresh_timer.interval() == MET_REFRESH_MS