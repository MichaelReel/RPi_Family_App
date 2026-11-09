"""Tests for SwappingContainerWidget."""
import pytest

from PyQt6.QtWidgets import QLabel, QWidget

from lib.widgets.swapping_container import SwappingContainerWidget


def test_swapping_container_starts_on_first_page(qtbot) -> None:
    """Widget should show the first widget on page 0 initially."""
    page1 = QLabel("Hello")
    page2 = QLabel("World")
    container = SwappingContainerWidget(pages=[page1, page2], swap_interval_ms=1000)
    qtbot.addWidget(container)
    container.show()

    assert container.stacked.currentIndex() == 0
    assert container.stacked.widget(0) is page1


def test_swapping_container_page_count(qtbot) -> None:
    """The stacked widget should have one page per widget in the list."""
    pages = [QLabel(f"Page {i}") for i in range(3)]
    container = SwappingContainerWidget(pages=pages, swap_interval_ms=1000)
    qtbot.addWidget(container)

    assert container.stacked.count() == 3


def test_swapping_container_cycles_pages(qtbot) -> None:
    """Advancing should cycle through all pages and wrap around."""
    pages = [QLabel(f"Page {i}") for i in range(3)]
    container = SwappingContainerWidget(pages=pages, swap_interval_ms=10)
    qtbot.addWidget(container)
    container.show()

    # Advance: 0 -> 1
    container._advance_page()
    assert container.stacked.currentIndex() == 1

    # Advance: 1 -> 2
    container._advance_page()
    assert container.stacked.currentIndex() == 2

    # Advance: 2 -> 0 (wrap around)
    container._advance_page()
    assert container.stacked.currentIndex() == 0


def test_swapping_container_timer_is_running(qtbot) -> None:
    """The swap timer should be running after initialisation."""
    container = SwappingContainerWidget(pages=[QLabel("test")], swap_interval_ms=5000)
    qtbot.addWidget(container)

    assert container._swap_timer.isActive()


def test_swapping_container_rejects_empty_list() -> None:
    """Passing an empty list should raise ValueError."""
    with pytest.raises(ValueError, match="At least one page"):
        SwappingContainerWidget(pages=[], swap_interval_ms=1000)


def test_swapping_container_single_page(qtbot) -> None:
    """A single page should work and 'advancing' stays on the same page."""
    page = QLabel("Only")
    container = SwappingContainerWidget(pages=[page], swap_interval_ms=1000)
    qtbot.addWidget(container)

    assert container.stacked.count() == 1
    container._advance_page()
    assert container.stacked.currentIndex() == 0
