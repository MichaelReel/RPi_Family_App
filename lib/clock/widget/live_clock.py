import sys
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

class LiveClockWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Configure layout window
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle("Live Clock")
        self.resize(450, 320)

        # Spacing adjustments for strict distribution
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # 1. Top Element: Time (Large Font)
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.time_label.setMinimumHeight(80)
        
        # 2. Middle Element: Day of the week (Medium Font)
        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_label.setFont(QFont("Arial", 22))
        self.day_label.setMinimumHeight(40)

        # 3. Bottom Element: Date (Medium Font)
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setFont(QFont("Arial", 22))
        self.date_label.setMinimumHeight(40)

        # Assemble layout using equal dynamic layout spacers
        layout.addStretch(1) 
        layout.addWidget(self.time_label)
        layout.addStretch(1) 
        layout.addWidget(self.day_label)
        layout.addStretch(1) 
        layout.addWidget(self.date_label)
        layout.addStretch(1) 

        # Initialize Timer for live updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

        # Force initial text render
        self.update_clock()

    def update_clock(self):
        now = datetime.now()

        # Format hours/minutes and seconds separately
        hours_minutes = now.strftime("%H:%M")
        seconds = now.strftime("%S")
        
        # Build HTML string: color #aaaaaa makes it dimmer, and font-size drops it down from 48pt
        time_html = f'{hours_minutes}<span style="color: #444444; font-size: 34pt;">:{seconds}</span>'
        
        day_text = now.strftime("%A")
        date_text = now.strftime("%d/%m/%Y")

        # Update labels
        self.time_label.setText(time_html)
        self.day_label.setText(day_text)
        self.date_label.setText(date_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = LiveClockWidget()
    clock.show()
    sys.exit(app.exec())
