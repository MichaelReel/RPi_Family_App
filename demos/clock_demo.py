import sys

from PyQt6.QtWidgets import QApplication

from lib.clock.widgets.live_clock import LiveClockWidget


def main() -> None:

    bg_color: str = "#ffffff"
    text_color: str = "#222222"

    app: QApplication = QApplication(sys.argv)
    app.setStyleSheet(f"background-color: {bg_color};color: {text_color};")

    clock_widget: LiveClockWidget = LiveClockWidget()
    clock_widget.show()

    app.exec()


if __name__ == "__main__":
    main()
