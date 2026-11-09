"""Generic widget that periodically swaps a contained widget with a blank placeholder."""
from logging import Logger, getLogger
from typing import Final

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

_LOGGER: Final[Logger] = getLogger(__name__)


class SwappingContainerWidget(QWidget):
    """A container that periodically swaps between a content widget and a blank placeholder.

    Uses a QStackedWidget with two pages:
    - Page 0: the provided content widget
    - Page 1: a blank placeholder widget

    A QTimer toggles between them at the configured interval.
    """

    def __init__(
        self,
        content: QWidget,
        swap_interval_ms: int,
        bg_color: str = "#000022",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._bg_color: str = bg_color

        outer_layout: QVBoxLayout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        self.setLayout(outer_layout)

        self.stacked: QStackedWidget = QStackedWidget()
        outer_layout.addWidget(self.stacked)

        # Page 1: blank placeholder
        self._blank_page: QWidget = QWidget()
        self._blank_page.setStyleSheet(f"background-color: {bg_color};")

        # Add pages to stacked widget
        self.stacked.addWidget(content)
        self.stacked.addWidget(self._blank_page)

        # Start on the content page
        self.stacked.setCurrentIndex(0)

        # Timer to swap views
        self._swap_timer: QTimer = QTimer(self)
        self._swap_timer.timeout.connect(self._swap_view)
        self._swap_timer.start(swap_interval_ms)

    def _swap_view(self) -> None:
        """Toggle between the content page (0) and blank page (1)."""
        current: int = self.stacked.currentIndex()
        self.stacked.setCurrentIndex(1 if current == 0 else 0)
