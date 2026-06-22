import sys

from PyQt6.QtWidgets import QApplication

from lib.clock.widget.live_clock import LiveClockWidget


def main() -> None:
    app: QApplication = QApplication(sys.argv)
    widget_window: LiveClockWidget = LiveClockWidget()
    widget_window.show()

    app.exec()

if __name__ == "__main__":
    main()