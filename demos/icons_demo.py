from typing import Final

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from lib.metoffice.icons import load_weather_icons

ICON_GRID_COLUMNS: Final[int] = 4
ICON_SIZE: Final[int] = 64
ICON_GRID_SPACING: Final[int] = 20


class WeatherViewerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Met Office Icon Gallery")
        self.resize(800, 600)

        scroll_area = self._build_scroll_area()
        self.setCentralWidget(scroll_area)

        # Load your specific icon dataset
        icons_dict = load_weather_icons()

        content_widget = scroll_area.widget()
        grid_layout = QGridLayout(content_widget)
        grid_layout.setSpacing(ICON_GRID_SPACING)

        for index, (code, pixmap) in enumerate(icons_dict.items()):
            row = index // ICON_GRID_COLUMNS
            col = index % ICON_GRID_COLUMNS
            grid_layout.addWidget(self._build_icon_cell(code, pixmap), row, col)

    def _build_scroll_area(self) -> QScrollArea:
        """Build the scrollable container with an empty content widget."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(QWidget())
        return scroll_area

    def _build_icon_cell(self, code: int, pixmap: QPixmap) -> QWidget:
        """Build a single grid cell: scaled icon (or null placeholder) + metadata."""
        cell_widget = QWidget()
        cell_layout = QVBoxLayout(cell_widget)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        image_label = QLabel()
        if not pixmap.isNull():
            # Scale smoothly to ICON_SIZE x ICON_SIZE while preserving ratio
            scaled_pixmap = pixmap.scaled(
                ICON_SIZE,
                ICON_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("⚠️ [Null]")

        text_label = QLabel(f"Code {code}\n{pixmap.width()}x{pixmap.height()} px")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("color: #666; font-size: 11px;")

        cell_layout.addWidget(image_label)
        cell_layout.addWidget(text_label)
        return cell_widget


if __name__ == "__main__":
    app = QApplication([])
    window = WeatherViewerWindow()
    window.show()
    app.exec()
