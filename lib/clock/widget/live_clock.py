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
        self._build_ui()

    def _build_ui(self) -> None:
        """Assemble the window, labels, layout and live-update timer."""
        self.setWindowTitle("Live Clock")
        self.resize(450, 320)
        self._build_labels()
        self._build_layout()
        self._start_timer()
        self.update_clock()

    def _build_labels(self) -> None:
        """Create the time, day and date labels, all centre-aligned."""
        self._time_label = QLabel()
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._day_label = QLabel()
        self._day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._date_label = QLabel()
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _build_layout(self) -> None:
        """Assemble the vertical layout with equal spacing between sections."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        layout.addStretch(1)
        layout.addWidget(self._time_label)
        layout.addStretch(1)

        if self._include_day:
            layout.addWidget(self._day_label)
            layout.addStretch(1)

        if self._include_date:
            layout.addWidget(self._date_label)
            layout.addStretch(1)

        self.setLayout(layout)

    def _start_timer(self) -> None:
        """Start the timer that drives live clock updates every second."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_clock)
        self._timer.start(1000)

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        """Automatically recalculates font sizes whenever the widget is resized."""
        super().resizeEvent(event)

        # Determine base scale using window height (prevents text clipping)
        base_height = self.height()
        time_font_size, sub_font_size, seconds_font_size = self._compute_font_sizes(
            base_height
        )
        self._seconds_font_size = seconds_font_size  # Saved for the inline HTML string

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

    def _compute_font_sizes(self, base_height: int) -> tuple[int, int, int]:
        """Calculate proportional pixel font sizes from the widget height.

        Returns ``(time_font_size, sub_font_size, seconds_font_size)``.
        The seconds size is stored separately for use in the inline HTML clock string.
        """
        time_font_size = max(16, int(base_height * 0.5))  # % of widget height
        sub_font_size = max(10, int(base_height * 0.07))  # % of widget height
        seconds_font_size = max(12, int(base_height * 0.11))
        return time_font_size, sub_font_size, seconds_font_size

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
