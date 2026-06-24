import pytest
from datetime import datetime
from unittest.mock import patch  # Built-in standard library module
from PyQt6.QtCore import Qt

from lib.clock.widget.live_clock import LiveClockWidget 

def test_clock_initial_values(qtbot):
    """Test using only built-in Python mocking tools."""
    
    # Freeze the time to a specific target point
    fixed_time = datetime(2026, 6, 22, 14, 30, 45) 

    # Use Python's built-in patch context manager to mock datetime
    with patch('lib.clock.widget.live_clock.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_time

        # Initialize the widget inside the mocked context window
        bg_color: str = "#ffffff"
        text_color: str = "#222222"
        seconds_color: str = "#444444"

        widget = LiveClockWidget()
        qtbot.addWidget(widget)
        widget.update_clock()

    # Assert standard text outputs
    assert widget.day_label.text() == "Monday"
    assert widget.date_label.text() == "22/06/2026"

    # Assert hours, minutes, and the dim smaller seconds tag
    expected_time_html = '14:30<span style="color: #444444; font-size: 34px;">:45</span>'
    assert widget.time_label.text() == expected_time_html
