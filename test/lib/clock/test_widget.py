from datetime import datetime
from unittest.mock import patch  # Built-in standard library module

from pytestqt.qtbot import QtBot

from lib.clock.widgets.live_clock import LiveClockWidget


def test_clock_initial_values(qtbot: QtBot) -> None:
    """Test using only built-in Python mocking tools."""

    # Freeze the time to a specific target point
    fixed_time = datetime(2026, 6, 22, 14, 30, 45)

    # Use Python's built-in patch context manager to mock datetime
    with patch("lib.clock.widgets.live_clock.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_time

        # Initialize the widget inside the mocked context window

        widget = LiveClockWidget()
        qtbot.addWidget(widget)
        widget.update_clock()

    # Assert standard text outputs (widget sets HTML with <span> tags for colouring)
    assert widget._day_label.text() == "<span style='color: #000000;'>Monday</span>"
    assert widget._date_label.text() == "<span style='color: #000000;'>22/06/2026</span>"

    # Assert hours, minutes, and the dim smaller seconds tag
    expected_time_html = '<span style="color: #000000;">14:30</span><span style="color: #000000; font-size: 34px;">:45</span>'
    assert widget._time_label.text() == expected_time_html
