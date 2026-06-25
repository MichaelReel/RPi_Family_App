from pathlib import Path
from PyQt6.QtGui import QPixmap

# 1. Define the dictionary mapping Met Office codes to the repo's file names
MET_OFFICE_ICON_MAP = {
    0: "00_clearsky_night.png",
    1: "01_clearsky_day.png",
    2: "02_partlycloudy_night.png",
    3: "03_partlycloudy_day.png",
    5: "05_mist.png",
    6: "06_fog.png",
    7: "07_cloudy.png",
    8: "08_overcast.png",
    9: "09_lightrainshowers_night.png",
    10: "10_lightrainshowers_day.png",
    11: "11_drizzle.png",
    12: "12_lightrain.png",
    13: "13_heavyrainshowers_night.png",
    14: "14_heavyrainshowers_day.png",
    15: "15_heavyrain.png",
    16: "16_lightsleetshowers_night.png",
    17: "17_lightsleetshowers_day.png",
    18: "18_sleet.png",
    19: "19_sleetshowers_night.png",
    20: "20_sleetshowers_day.png",
    21: "21_hail.png",
    22: "22_lightsnowshowers_night.png",
    23: "23_lightsnowshowers_day.png",
    24: "24_lightsnow.png",
    25: "25_heavysnowshowers_night.png",
    26: "26_heavysnowshowers_day.png",
    27: "27_heavysnow.png",
    28: "28_rainshowersandthunder_night.png",
    29: "29_rainshowersandthunder_day.png",
    30: "30_heavyrainandthunder.png",
}

def load_weather_icons(
    directory_path: str | Path = "lib/metoffice/icons/weather/"
) -> dict[int, QPixmap]:
    """Loads all weather icons into memory as QPixmaps indexed by Met Office code."""
    icon_dir: Path = Path(directory_path)
    loaded_icons: dict[int, QPixmap] = {}
    
    # Cache unique images to avoid loading the same file multiple times (e.g., fog/mist)
    pixmap_cache: dict[str, QPixmap] = {}

    code: int
    filename: str
    for code, filename in MET_OFFICE_ICON_MAP.items():
        file_path: Path = icon_dir / filename
        
        # Check cache first for reused icons
        if filename in pixmap_cache:
            loaded_icons[code] = pixmap_cache[filename]
            continue
            
        # Load from disk if it's the first time seeing this file
        if file_path.exists():
            pixmap: QPixmap = QPixmap(str(file_path))
            pixmap_cache[filename] = pixmap
            loaded_icons[code] = pixmap
        else:
            print(f"Warning: Missing icon file {file_path}")
            # Optional: loaded_icons[code] = pixmap_cache.get("default.png")
            
    return loaded_icons
