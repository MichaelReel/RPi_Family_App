import os
from datetime import date, datetime, timezone

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from lib.metoffice.models import DailyForecastPoint
from lib.metoffice.icons import load_weather_icons


class DayCardWidget(QFrame):
    """Displays specific daily weather metrics from a DailyForecastPoint with custom asset icons."""
    
    # Class-level cache so we don't reload files from disk for every new card instance
    _icon_cache: dict[int, QPixmap] = {}

    def __init__(self, data: DailyForecastPoint, parent=None) -> None:
        super().__init__(parent)
        
        # Initialize the static cache once if it's empty
        if not DayCardWidget._icon_cache:
            DayCardWidget._icon_cache = load_weather_icons()
        
        # Check if this card's date is today
        forecast_date_utc: date = data.date.astimezone(timezone.utc).date()
        current_date_utc: date = datetime.now(timezone.utc).date()
        self.is_today: bool = (forecast_date_utc == current_date_utc)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # 1. Initialize main weather elements
        self.lbl_date: QLabel = QLabel()
        self.lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_icon: QLabel = QLabel()
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_cond: QLabel = QLabel()
        self.lbl_cond.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 2. Initialize metrics row elements (Image Labels + Value Labels)
        self.ico_temp: QLabel = QLabel()
        self.lbl_temps: QLabel = QLabel()
        
        self.ico_feels: QLabel = QLabel()
        self.lbl_feels: QLabel = QLabel()
        
        self.ico_rain: QLabel = QLabel()
        self.lbl_rain: QLabel = QLabel()
        
        self.ico_uv: QLabel = QLabel()
        self.lbl_uv: QLabel = QLabel()
        
        # Ensure image containers and data align cleanly
        self.ico_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ico_feels.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ico_rain.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ico_uv.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_temps.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_feels.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_rain.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_uv.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # 3. Build the visual layout skeleton
        layout: QVBoxLayout = QVBoxLayout()
        layout.setSpacing(6)
        layout.addWidget(self.lbl_date)
        layout.addWidget(self.lbl_icon) 
        layout.addWidget(self.lbl_cond)
        layout.addSpacing(4)
        
        # Helper to construct clean horizontal rows for metrics
        def create_metric_row(ico: QLabel, lbl: QLabel) -> QHBoxLayout:
            row = QHBoxLayout()
            row.setSpacing(8)             
            row.setAlignment(Qt.AlignmentFlag.AlignCenter) 
            row.addWidget(ico)
            row.addWidget(lbl)
            return row

        layout.addLayout(create_metric_row(self.ico_temp, self.lbl_temps))
        layout.addLayout(create_metric_row(self.ico_feels, self.lbl_feels))
        layout.addLayout(create_metric_row(self.ico_rain, self.lbl_rain))
        layout.addLayout(create_metric_row(self.ico_uv, self.lbl_uv))
        
        self.setLayout(layout)

        # 4. Populate metrics, load images, and apply targeted styling
        self.update_data(data)

    def paintEvent(self, event):
        """Mandatory boilerplate for custom QFrame subclasses to support stylesheets."""
        from PyQt6.QtGui import QPainter
        from PyQt6.QtWidgets import QStyle, QStyleOption
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)

    def _set_metric_icon(self, label: QLabel, filename: str, size: int = 16) -> None:
        """Helper to safely load, scale, and assign an image asset to a label."""
        # Update path structure to match your project files structure if needed
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "assets", "icons", filename)
        
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                size, size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(scaled)
        else:
            # Fallback character if image file is broken or missing
            label.setText("▪")

    def update_data(self, data: DailyForecastPoint) -> None:
        """Updates the widget styles, text metrics, and icons with new forecast data."""
        
        icon_dim: int = 400 if self.is_today else 100
        cond_font_size: str = "80px" if self.is_today else "20px"
        
        self.lbl_icon.setMinimumSize(icon_dim, icon_dim)

        if self.is_today:
            self.setStyleSheet("DayCardWidget { background-color: #ebf5ff; border: 2px solid #007bff; border-radius: 8px; }")
            label_text_color = "#111111"
        else:
            self.setStyleSheet("DayCardWidget { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 6px; }")
            label_text_color = "#222222"
            
        font_family = "font-family: Arial, sans-serif;"
        
        self.lbl_date.setStyleSheet(f"{font_family} font-weight: bold; font-size: 14px; color: #0056b3;")
        self.lbl_cond.setStyleSheet(f"{font_family} color: #cccccc; font-weight: 500; font-size: {cond_font_size};")
        
        metrics_style = f"{font_family} color: {label_text_color}; font-size: 13px;"
        self.lbl_temps.setStyleSheet(metrics_style)
        self.lbl_feels.setStyleSheet(metrics_style)
        self.lbl_rain.setStyleSheet(metrics_style)
        self.lbl_uv.setStyleSheet(metrics_style)
        
        # Populate text values cleanly
        def fmt(val, suffix="") -> str:
            return f"{val}{suffix}" if val is not None else "--"

        self.lbl_date.setText(data.date.strftime("%A, %b %d"))
        self.lbl_cond.setText(data.weather_condition)
        
        self.lbl_temps.setText(f"{fmt(data.max_temperature_c, '°')} / {fmt(data.min_temperature_c, '°')}")
        self.lbl_feels.setText(fmt(data.max_feels_like_c, "°C"))
        self.lbl_rain.setText(fmt(data.rain_probability_pct, "%"))
        self.lbl_uv.setText(fmt(data.uv_index_max))

        # 5. Load the custom metric images from disk
        # Adjust filenames matching your actual files (e.g., png or svg)
        self._set_metric_icon(self.ico_temp, "temp.png", size=16)
        self._set_metric_icon(self.ico_feels, "feels.png", size=16)
        self._set_metric_icon(self.ico_rain, "rain.png", size=16)
        self._set_metric_icon(self.ico_uv, "uv.png", size=16)

        # Main Weather Graphic handler
        weather_code = getattr(data, "weather_code", None)
        pixmap = self._icon_cache.get(weather_code)

        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                icon_dim, icon_dim, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_icon.setPixmap(scaled_pixmap)
        else:
            self.lbl_icon.setText("❓")
