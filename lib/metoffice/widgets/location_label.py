"""Small widget that displays the location name from a weather report."""
from logging import Logger, getLogger
from typing import Final

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget

_LOGGER: Final[Logger] = getLogger(__name__)

# Default style — can be overridden by the caller
_DEFAULT_STYLE: str = (
    "QLabel { "
    "    background-color: transparent; "
    "    color: #888888; "
    "    font-size: 14px; "
    "    font-family: Arial, sans-serif; "
    "}"
)


class LocationLabelWidget(QWidget):
    """Displays the location name above the weather grid.

    The location name is passed as a string (fetched once at startup), so this
    widget does not make any API calls itself.
    """

    def __init__(
        self,
        location_name: str | None,
        style: str = _DEFAULT_STYLE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._style: str = style

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(self._style)

        layout = self.layout()
        if layout is None:
            from PyQt6.QtWidgets import QVBoxLayout

            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(layout)

        layout.addWidget(self.label)

        if location_name:
            self.label.setText(location_name)
            self.label.setVisible(True)
        else:
            self.label.setVisible(False)
