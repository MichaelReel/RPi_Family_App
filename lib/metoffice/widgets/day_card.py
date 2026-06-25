from datetime import date, datetime, timezone

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from lib.metoffice.models import DailyForecastPoint
from lib.metoffice.icons import load_weather_icons


class DayCardWidget(QFrame):
    """Displays specific daily weather metrics from a DailyForecastPoint with an icon."""
    
    # Class-level cache so we don't reload files from disk for every new card instance
    _icon_cache: dict[int, QPixmap] = {}

    def __init__(self, data: DailyForecastPoint, parent=None) -> None:
        super().__init__(parent)
        
        # Initialize the static cache once if it's empty
        if not DayCardWidget._icon_cache:
            DayCardWidget._icon_cache = load_weather_icons()
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # 1. Initialize empty UI structures first
        self.lbl_date: QLabel = QLabel()
        self.lbl_date.setStyleSheet("font-weight: bold; font-size: 14px; color: #0056b3;")
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # NEW: Dedicated large visual layout container for the weather graphic
        self.lbl_icon: QLabel = QLabel()
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setMinimumSize(64, 64)  # reserves clean layout space
        
        self.lbl_cond: QLabel = QLabel()
        self.lbl_cond.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.lbl_cond.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_temps: QLabel = QLabel()
        self.lbl_feels: QLabel = QLabel()
        self.lbl_rain: QLabel = QLabel()
        self.lbl_uv: QLabel = QLabel()
        
        # 2. Build the visual layout skeleton
        layout: QVBoxLayout = QVBoxLayout()
        layout.setSpacing(6)
        layout.addWidget(self.lbl_date)
        layout.addWidget(self.lbl_icon)  # Inserted here to give it visual prominence
        layout.addWidget(self.lbl_cond)
        layout.addSpacing(4)
        layout.addWidget(self.lbl_temps)
        layout.addWidget(self.lbl_feels)
        layout.addWidget(self.lbl_rain)
        layout.addWidget(self.lbl_uv)
        
        self.setLayout(layout)

        # 3. Populate and style the widget using the initial data
        self.update_data(data)

    def update_data(self, data: DailyForecastPoint) -> None:
        """Updates the widget styles and text metrics with new forecast data."""
        # Check if this card's date is today
        forecast_date_utc: date = data.date.astimezone(timezone.utc).date()
        current_date_utc: date = datetime.now(timezone.utc).date()
        is_today: bool = (forecast_date_utc == current_date_utc)

        # Dynamic Style sheet selection based on timezone-safe match
        if is_today:
            self.setStyleSheet("""
                DayCardWidget {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ebf5ff, stop:1 #ffffff);
                    border: 2px solid #007bff;
                    border-radius: 8px;
                }
                QLabel {
                    color: #111111;
                    font-family: Arial, sans-serif;
                }
            """)
        else:
            self.setStyleSheet("""
                DayCardWidget {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 6px;
                }
                QLabel {
                    color: #222222;
                    font-family: Arial, sans-serif;
                }
            """)
        
        # Safe string formatting helper for optional fields
        def fmt(val, suffix="") -> str:
            return f"{val}{suffix}" if val is not None else "--"

        date_str: str = data.date.strftime("%A, %b %d")
        high: str = fmt(data.max_temperature_c, "°C")
        low: str = fmt(data.min_temperature_c, "°C")
        feels: str = fmt(data.max_feels_like_c, "°C")
        rain: str = fmt(data.rain_probability_pct, "%")
        uv: str = fmt(data.uv_index_max)
        
        # Refresh label values
        self.lbl_date.setText(date_str)
        self.lbl_cond.setText(data.weather_condition)
        self.lbl_temps.setText(f"High: {high}  |  Low: {low}")
        self.lbl_feels.setText(f"Feels like: {feels}")
        self.lbl_rain.setText(f"🌧️ Rain Chance: {rain}")
        self.lbl_uv.setText(f"☀️ Max UV Index: {uv}")

        # NEW: Fetch and apply the icon from memory cache using code data endpoint
        # Adjust `data.weather_code` if your model uses a different property name
        weather_code = getattr(data, "weather_code", None)
        pixmap = self._icon_cache.get(weather_code)

        if pixmap and not pixmap.isNull():
            # Scale smoothly to 64x64 (or 72x72 / 96x96 for a larger UI look)
            scaled_pixmap = pixmap.scaled(
                64, 64, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_icon.setPixmap(scaled_pixmap)
        else:
            # Clean fallback state if the file is missing or code is null
            self.lbl_icon.setText("❓")