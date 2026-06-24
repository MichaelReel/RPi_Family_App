from PyQt6.QtWidgets import QApplication, QBoxLayout, QMainWindow, QPushButton, QWidget

from lib.clock.widget.live_clock import LiveClockWidget
from lib.metoffice.client import get_human_readable_weather
from lib.metoffice.widgets.eight_day_grid import EightDayGridWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Full Screen App")
        # self.resize(400, 600)

        button = QPushButton("Exit")
        button.pressed.connect(self.close)
        # self.setCentralWidget(button)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom, central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)


        bg_color: str = "#000022"
        text_color: str = "#0000aa"

        self.setStyleSheet(f"background-color: {bg_color};color: {text_color};")

        self.clock_widget: LiveClockWidget = LiveClockWidget()
        self.met_office_widget: EightDayGridWidget = EightDayGridWidget(report_source=get_human_readable_weather)

        self.main_layout.addWidget(self.clock_widget)
        self.main_layout.addWidget(self.met_office_widget)
        self.main_layout.addWidget(button)

        self.showFullScreen()


def main():
    app = QApplication([])
    window = MainWindow()
    app.exec()


if __name__ == "__main__":
    main()
