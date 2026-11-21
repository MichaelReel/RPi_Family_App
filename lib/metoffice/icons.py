from collections.abc import Mapping
from logging import Logger, getLogger
from pathlib import Path
from typing import Final

from PyQt6.QtGui import QPixmap

_LOGGER: Final[Logger] = getLogger(__name__)

# 1. Define the dictionary mapping Met Office codes to the repo's file names
_MET_OFFICE_WEATHER_MAP: Final[dict[int, str]] = {
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

_MET_OFFICE_STATS_MAP: Final[dict[str, str]] = {
    "rain_pct": "precipitation.png",
    "temp_high": "temp_high.png",
    "temp_low": "temp_low.png",
    "temp_feel": "temp_feels.png",
    "uv_index": "uv.png",
    "wind": "wind.png",
}


def _load_icons[T](
    code_to_filename: Mapping[T, str], icon_dir: Path
) -> dict[T, QPixmap]:
    """Load a mapping of codes/keys to icon file names into a cache of QPixmaps.

    Reused file names are loaded from disk only once (e.g. fog/mist, temp_high/feel),
    with the resulting QPixmap shared across every key that references it. Missing
    files are logged and skipped.
    """
    loaded_icons: dict[T, QPixmap] = {}
    pixmap_cache: dict[str, QPixmap] = {}

    for code, filename in code_to_filename.items():
        if filename in pixmap_cache:
            loaded_icons[code] = pixmap_cache[filename]
            continue

        file_path = icon_dir / filename
        if file_path.exists():
            pixmap = QPixmap(str(file_path))
            pixmap_cache[filename] = pixmap
            loaded_icons[code] = pixmap
        else:
            _LOGGER.warning("Missing icon file: %s", file_path)

    return loaded_icons


class _IconCaches:
    """Singleton cache for weather and stats icons.

    All icon pixmaps are loaded once and reused across DayCardWidget instances
    to avoid repeated disk I/O. The module-level `_caches` singleton is the
    canonical source — do not create additional instances.
    """

    def __init__(self) -> None:
        self._loaded_weather_icons: dict[int, QPixmap] = {}
        self._loaded_stats_icons: dict[str, QPixmap] = {}

        self._weather_icons_loaded: bool = False
        self._stats_icons_loaded: bool = False

    def load_weather_icons(self, directory_path: str | Path) -> dict[int, QPixmap]:
        """Loads all weather icons into memory as QPixmaps indexed by Met Office code."""
        if self._weather_icons_loaded:
            return self._loaded_weather_icons

        self._loaded_weather_icons = _load_icons(
            _MET_OFFICE_WEATHER_MAP, Path(directory_path)
        )
        self._weather_icons_loaded = True
        return self._loaded_weather_icons

    def load_stats_icons(self, directory_path: str | Path) -> dict[str, QPixmap]:
        """Loads all stats icons into memory as QPixmaps indexed by Met Office code."""
        if self._stats_icons_loaded:
            return self._loaded_stats_icons

        self._loaded_stats_icons = _load_icons(
            _MET_OFFICE_STATS_MAP, Path(directory_path)
        )
        self._stats_icons_loaded = True
        return self._loaded_stats_icons

    def invalidate_caches(self) -> None:
        """Reset both weather and stats icon caches to their empty, unloaded state.

        Useful for tests and for runtime scenarios where the icon directory may
        have changed and the cache needs to be refreshed.
        """
        self._loaded_weather_icons = {}
        self._loaded_stats_icons = {}
        self._weather_icons_loaded = False
        self._stats_icons_loaded = False


_caches: _IconCaches = _IconCaches()


def load_weather_icons(
    directory_path: str | Path = "lib/metoffice/icons/weather/",
) -> dict[int, QPixmap]:
    return _caches.load_weather_icons(directory_path=directory_path)


def load_stats_icons(
    directory_path: str | Path = "lib/metoffice/icons/stats/",
) -> dict[str, QPixmap]:
    return _caches.load_stats_icons(directory_path=directory_path)
