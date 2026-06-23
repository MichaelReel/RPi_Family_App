from PySide6.QtWidgets import QApplication, QBoxLayout, QMainWindow, QPushButton, QWidget

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

        self.clock_widget: LiveClockWidget = LiveClockWidget()
        self.met_office_widget: EightDayGridWidget = EightDayGridWidget(report_source=get_human_readable_weather)

        self.main_layout.addWidget(self.clock_widget)
        self.main_layout.addWidget(self.met_office_widget)
        self.main_layout.addWidget(button)

        self.showFullScreen()
        # self.show()

    # def resizeEvent(self, event) -> None:
    #     """Monitors window size and swaps layout direction based on aspect ratio."""
    #     super().resizeEvent(event)
        
    #     size = event.size()
    #     # Landscape: Width is greater than or equal to height
    #     if size.width() >= size.height():
    #         if self.main_layout.direction() != QBoxLayout.Direction.LeftToRight:
    #             self.main_layout.setDirection(QBoxLayout.Direction.LeftToRight)
    #     # Portrait: Height is greater than width
    #     else:
    #         if self.main_layout.direction() != QBoxLayout.Direction.TopToBottom:
    #             self.main_layout.setDirection(QBoxLayout.Direction.TopToBottom)


def main():
    app = QApplication([])
    window = MainWindow()
    app.exec()


if __name__ == "__main__":
    main()
