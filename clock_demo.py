import sys

from PyQt6.QtWidgets import QApplication

from lib.clock.widget.live_clock import LiveClockWidget


def main() -> None:

    bg_color: str = "#ffffff"
    text_color: str = "#222222"
    seconds_color: str = "#444444"

    app: QApplication = QApplication(sys.argv)
    app.setStyleSheet(f"background-color: {bg_color};color: {text_color};")

    widget_window: LiveClockWidget = LiveClockWidget()
    widget_window.show()

    app.exec()

if __name__ == "__main__":
    main()