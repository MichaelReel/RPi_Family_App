"""Generic widget that periodically cycles through a list of contained widgets."""
from logging import Logger, getLogger
from typing import Final

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

_LOGGER: Final[Logger] = getLogger(__name__)


class SwappingContainerWidget(QWidget):
    """A container that periodically cycles through a list of widgets.

    Uses a QStackedWidget with one page per widget in the provided list.
    A QTimer advances to the next widget on each tick, wrapping around
    to the first widget after the last one.
    """

    def __init__(
        self,
        pages: list[QWidget],
        swap_interval_ms: int,
        bg_color: str = "#000022",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._bg_color: str = bg_color
        self._page_count: int = len(pages)

        if self._page_count == 0:
            raise ValueError("At least one page widget must be provided")

        outer_layout: QVBoxLayout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        self.setLayout(outer_layout)

        self.stacked: QStackedWidget = QStackedWidget()
        outer_layout.addWidget(self.stacked)

        # Add all pages to the stacked widget
        for widget in pages:
            self.stacked.addWidget(widget)

        # Start on the first page
        self.stacked.setCurrentIndex(0)

        # Timer to advance pages
        self._swap_timer: QTimer = QTimer(self)
        self._swap_timer.timeout.connect(self._advance_page)
        self._swap_timer.start(swap_interval_ms)

    def _advance_page(self) -> None:
        """Advance to the next page, wrapping around to the first."""
        current: int = self.stacked.currentIndex()
        next_index: int = (current + 1) % self._page_count
        self.stacked.setCurrentIndex(next_index)
