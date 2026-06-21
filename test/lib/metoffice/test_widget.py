import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from PyQt6.QtWidgets import QApplication

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


def test_widget_initialization_and_card_count(qtbot, expected_human_report_snapshot):
    """Verifies grid container instantiates exactly 8 interior card objects."""
    grid_widget = EightDayGridWidget(expected_human_report_snapshot)
    qtbot.addWidget(grid_widget) # Registers the widget for auto-cleanup
    
    assert len(grid_widget.cards) == 8


def test_card_data_mapping_and_labels(qtbot, expected_human_report_snapshot):
    """Verifies data properties accurately map to visual text layouts."""
    grid_widget = EightDayGridWidget(expected_human_report_snapshot)
    qtbot.addWidget(grid_widget)
    
    first_card = grid_widget.cards[0]
    
    assert "High: 18.34°C" in first_card.lbl_temps.text()
    assert "Low: 8.43°C" in first_card.lbl_temps.text()
    assert first_card.lbl_cond.text() == "Cloudy"
    assert first_card.lbl_rain.text() == "🌧️ Rain Chance: 73%"


def test_dynamic_reflow_layout_columns(qtbot, expected_human_report_snapshot):
    """Verifies screen resize operations force the grid into 4x2 or 2x4 structures."""
    grid_widget = EightDayGridWidget(expected_human_report_snapshot)
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
