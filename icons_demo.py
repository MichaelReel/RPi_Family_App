import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from lib.metoffice.icons import load_weather_icons

class WeatherViewerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Met Office Icon Gallery")
        self.resize(800, 600)

        # Main scrollable container setup
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        # Grid configuration
        grid_layout = QGridLayout(content_widget)
        grid_layout.setSpacing(20)

        # Load your specific icon dataset
        icons_dict = load_weather_icons()

        # Build grid with exactly 4 columns
        max_columns = 4
        
        for index, (code, pixmap) in enumerate(icons_dict.items()):
            row = index // max_columns
            col = index % max_columns

            # Cell item layout
            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Icon visual component
            image_label = QLabel()
            if not pixmap.isNull():
                # Scale smoothly to 64x64 while preserving ratio
                scaled_pixmap = pixmap.scaled(
                    64, 64, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setText("⚠️ [Null]")

            # Title metadata layout
            text_label = QLabel(f"Code {code}\n{pixmap.width()}x{pixmap.height()} px")
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_label.setStyleSheet("color: #666; font-size: 11px;")

            cell_layout.addWidget(image_label)
            cell_layout.addWidget(text_label)
            
            grid_layout.addWidget(cell_widget, row, col)

if __name__ == "__main__":
    app = QApplication([])
    window = WeatherViewerWindow()
    window.show()
    app.exec()