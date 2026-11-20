from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QResizeEvent
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LiveClockWidget(QWidget):
    def __init__(
        self,
        hour_minutes_color: str = "#000000",
        seconds_color: str = "#000000",
        day_color: str = "#000000",
        date_color: str = "#000000",
        include_day: bool = True,
        include_date: bool = True,
    ):
        super().__init__()
        self._hour_minutes_color: str = hour_minutes_color
        self._seconds_color: str = seconds_color
        self._day_color: str = day_color
        self._date_color: str = date_color
        self._include_day: bool = include_day
        self._include_date: bool = include_date
        self._seconds_font_size: int = 34
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle("Live Clock")
        self.resize(450, 320)

        # Equal distribution spacing settings
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # 1. Top Element: Time
        self._time_label = QLabel()
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. Middle Element: Day of the week
        self._day_label = QLabel()
        self._day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 3. Bottom Element: Date
        self._date_label = QLabel()
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Assemble layout with identical spacing blocks
        layout.addStretch(1)
        layout.addWidget(self._time_label)
        layout.addStretch(1)

        if self._include_day:
            layout.addWidget(self._day_label)
            layout.addStretch(1)

        if self._include_date:
            layout.addWidget(self._date_label)
            layout.addStretch(1)

        # Initialize Timer for live updates
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_clock)
        self._timer.start(1000)

        self.update_clock()

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        """Automatically recalculates font sizes whenever the widget is resized."""
        super().resizeEvent(event)

        # Determine base scale using window height (prevents text clipping)
        base_height = self.height()

        # Calculate proportional pixel sizes
        time_font_size = max(16, int(base_height * 0.5))  # % of widget height
        sub_font_size = max(10, int(base_height * 0.07))  # % of widget height
        self._seconds_font_size = max(
            12, int(base_height * 0.11)
        )  # Saved for HTML string

        # Update widget fonts and minimum heights dynamically
        time_font = QFont("Arial", time_font_size, QFont.Weight.Bold)
        sub_font = QFont("Arial", sub_font_size)

        self._time_label.setFont(time_font)
        self._time_label.setMinimumHeight(int(base_height * 0.25))

        self._day_label.setFont(sub_font)
        self._day_label.setMinimumHeight(int(base_height * 0.12))

        self._date_label.setFont(sub_font)
        self._date_label.setMinimumHeight(int(base_height * 0.12))

        # Refresh the clock text instantly to apply the new inline HTML size
        self.update_clock()

    def update_clock(self) -> None:
        now = datetime.now()  # noqa: DTZ005

        hours_minutes = now.strftime("%H:%M")
        seconds = now.strftime("%S")

        sec_size = self._seconds_font_size

        # Inject dynamic pixel sizing (px) into the HTML instead of static points (pt)
        hh_mm_html: str = (
            f'<span style="color: {self._hour_minutes_color};">{hours_minutes}</span>'
        )
        time_html: str = f'{hh_mm_html}<span style="color: {self._seconds_color}; font-size: {sec_size}px;">:{seconds}</span>'

        day_text: str = (
            f"<span style='color: {self._day_color};'>{now.strftime('%A')}</span>"
        )
        date_text: str = f"<span style='color: {self._date_color};'>{now.strftime('%d/%m/%Y')}</span>"

        self._time_label.setText(time_html)
        self._day_label.setText(day_text)
        self._date_label.setText(date_text)
