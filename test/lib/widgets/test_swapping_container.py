"""Tests for SwappingContainerWidget."""
import pytest

from PyQt6.QtWidgets import QLabel, QWidget

from lib.widgets.swapping_container import SwappingContainerWidget


def test_swapping_container_starts_on_content(qtbot) -> None:
    """Widget should show the content widget on page 0 initially."""
    content = QLabel("Hello")
    container = SwappingContainerWidget(content=content, swap_interval_ms=1000)
    qtbot.addWidget(container)
    container.show()

    assert container.stacked.currentIndex() == 0
    assert container.stacked.widget(0) is content


def test_swapping_container_blank_page_exists(qtbot) -> None:
    """The stacked widget should have exactly 2 pages."""
    content = QLabel("Hello")
    container = SwappingContainerWidget(content=content, swap_interval_ms=1000)
    qtbot.addWidget(container)

    assert container.stacked.count() == 2


def test_swapping_container_toggles_on_timeout(qtbot) -> None:
    """Swapping between content and blank page should toggle on each timeout."""
    content = QLabel("Hello")
    container = SwappingContainerWidget(content=content, swap_interval_ms=10)
    qtbot.addWidget(container)
    container.show()

    # First swap → blank page
    container._swap_view()
    assert container.stacked.currentIndex() == 1

    # Second swap → back to content
    container._swap_view()
    assert container.stacked.currentIndex() == 0


def test_swapping_container_timer_is_running(qtbot) -> None:
    """The swap timer should be running after initialisation."""
    content = QLabel("Hello")
    container = SwappingContainerWidget(content=content, swap_interval_ms=5000)
    qtbot.addWidget(container)

    assert container._swap_timer.isActive()


def test_swapping_container_blank_has_bg_color(qtbot) -> None:
    """The blank page should have the specified background colour."""
    content = QLabel("Hello")
    container = SwappingContainerWidget(
        content=content,
        swap_interval_ms=1000,
        bg_color="#AABBCC",
    )
    qtbot.addWidget(container)

    assert "#AABBCC" in container._blank_page.styleSheet()