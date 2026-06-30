from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

class LiveClockWidget(QWidget):
    def __init__(self, seconds_color: str = "#000000"):
        super().__init__()
        self._seconds_color: str = seconds_color
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle("Live Clock")
        self.resize(450, 320)

        # Equal distribution spacing settings
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # 1. Top Element: Time
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 2. Middle Element: Day of the week
        self.day_label = QLabel()
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 3. Bottom Element: Date
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Assemble layout with identical spacing blocks
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

        self.update_clock()
    
    def resizeEvent(self, event):
        """Automatically recalculates font sizes whenever the widget is resized."""
        super().resizeEvent(event)
        
        # Determine base scale using window height (prevents text clipping)
        base_height = self.height()

        # Calculate proportional pixel sizes
        time_font_size = max(16, int(base_height * 0.3))   # % of widget height
        sub_font_size = max(10, int(base_height * 0.07))    # % of widget height
        self.seconds_font_size = max(12, int(base_height * 0.11)) # Saved for HTML string

        # Update widget fonts and minimum heights dynamically
        time_font = QFont("Arial", time_font_size, QFont.Weight.Bold)
        sub_font = QFont("Arial", sub_font_size)

        self.time_label.setFont(time_font)
        self.time_label.setMinimumHeight(int(base_height * 0.25))

        self.day_label.setFont(sub_font)
        self.day_label.setMinimumHeight(int(base_height * 0.12))

        self.date_label.setFont(sub_font)
        self.date_label.setMinimumHeight(int(base_height * 0.12))

        # Refresh the clock text instantly to apply the new inline HTML size
        self.update_clock()

    def update_clock(self):
        now = datetime.now()

        hours_minutes = now.strftime("%H:%M")
        seconds = now.strftime("%S")
        
        # Check if font size variable exists yet (handles startup sequence)
        sec_size = getattr(self, 'seconds_font_size', 34)
        
        # Inject dynamic pixel sizing (px) into the HTML instead of static points (pt)
        time_html = f'{hours_minutes}<span style="color: {self._seconds_color}; font-size: {sec_size}px;">:{seconds}</span>'
        
        day_text = now.strftime("%A")
        date_text = now.strftime("%d/%m/%Y")

        self.time_label.setText(time_html)
        self.day_label.setText(day_text)
        self.date_label.setText(date_text)
