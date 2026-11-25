"""UI styling configuration (colours, fonts, card styles, graph palette).

Populated incrementally by T8.2–T8.8. Kept as a leaf module: it must not
import from ``lib`` so it can be imported by any widget without a cycle.
"""

from dataclasses import dataclass, field
from typing import Final

# App-wide colours (T8.2)
APP_BG_COLOR: Final[str] = "#000022"
APP_TEXT_COLOR: Final[str] = "#0000aa"
CLOCK_LABEL_COLOR: Final[str] = "#0000aa"
CLOCK_DAY_DATE_COLOR: Final[str] = "#0000FF"
CLOCK_SECONDS_COLOR: Final[str] = "#000088"

# Shared font family (T8.3)
UI_FONT_FAMILY: Final[str] = "Arial"


@dataclass
class UIElementStyle:
    """Holds individual CSS and font properties for a single text label."""

    font_family: str = f"{UI_FONT_FAMILY}, sans-serif"
    font_size: str = "13px"
    font_weight: str = "normal"
    text_color: str = "#888888"

    def to_stylesheet(self) -> str:
        """Generates a valid Qt Style Sheet string from properties."""
        return (
            f"font-family: {self.font_family}; "
            f"font-size: {self.font_size}; "
            f"font-weight: {self.font_weight}; "
            f"color: {self.text_color};"
        )


@dataclass
class CardStyleConfig:
    """Defines the complete visual representation of a weather card instance."""

    # Main Container Styling
    widget_stylesheet: str = (
        "DayCardWidget { background-color: #ffffff; border: 1px solid #cccccc; "
        "border-radius: 6px; }"
    )

    # Graphic and Layout Sizing
    weather_icon_dim: int = 100
    metric_icon_dim: int = 16
    layout_spacing: int = 6
    row_spacing: int = 8

    # Text Element Styles
    date_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(
            font_size="14px", font_weight="bold", text_color="#0056b3"
        )
    )
    condition_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(
            font_size="20px", font_weight="500", text_color="#cccccc"
        )
    )
    metrics_style: UIElementStyle = field(
        default_factory=lambda: UIElementStyle(font_size="13px", text_color="#888888")
    )


# Default card style (T8.4)
DEFAULT_DAY_CARD_STYLE: Final[CardStyleConfig] = CardStyleConfig()

# Four-day grid card styles (T8.5)
FEATURED_DAY_CARD_STYLE: Final[CardStyleConfig] = CardStyleConfig(
    widget_stylesheet=(
        "DayCardWidget { background-color: #000022; border: 0px solid #007bff; "
        "border-radius: 8px; }"
    ),
    weather_icon_dim=400,
    metric_icon_dim=38,
    layout_spacing=12,
    row_spacing=10,
    date_style=UIElementStyle(font_size="56px", font_weight="bold", text_color="#0000ff"),
    condition_style=UIElementStyle(font_size="80px", font_weight="500", text_color="#cccccc"),
    metrics_style=UIElementStyle(font_size="38px", text_color="#999999"),
)

SECONDARY_DAY_CARD_STYLE: Final[CardStyleConfig] = CardStyleConfig(
    widget_stylesheet=(
        "DayCardWidget { background-color: #000022; border: 1px solid #cccccc; "
        "border-radius: 6px; }"
    ),
    weather_icon_dim=100,
    metric_icon_dim=16,
    layout_spacing=6,
    row_spacing=8,
    date_style=UIElementStyle(font_size="14px", font_weight="bold", text_color="#0056b3"),
    condition_style=UIElementStyle(font_size="20px", font_weight="500", text_color="#cccccc"),
    metrics_style=UIElementStyle(font_size="13px", text_color="#888888"),
)

DAY_GRID_SPACING: Final[int] = 10

# Weather graph palette (T8.6)
GRAPH_TEMP_MAX_COLOR: Final[str] = "#FF6B6B"
GRAPH_TEMP_MIN_COLOR: Final[str] = "#4D96FF"
GRAPH_FEELS_LIKE_COLOR: Final[str] = "#FFB347"
GRAPH_RAIN_COLOR: Final[str] = "#4ECDC4"
GRAPH_UV_COLOR: Final[str] = "#FFD93D"
GRAPH_WIND_COLOR: Final[str] = "#95E1D3"
GRAPH_WIND_GUST_COLOR: Final[str] = "#FFFFFF"
GRAPH_AXIS_COLOR: Final[str] = "#555555"
GRAPH_TEXT_COLOR: Final[str] = "#cccccc"
GRAPH_GRID_COLOR: Final[str] = "#333355"
GRAPH_GRID_COLOR_STRONG: Final[str] = "#6A6A9A"
GRAPH_LANE_BORDER_COLOR: Final[str] = "#444466"
GRAPH_MIDNIGHT_COLOR: Final[str] = "#3A3A5C"
GRAPH_NOW_COLOR: Final[str] = "#E86A5E"

# Location label style (T8.7)
LOCATION_LABEL_STYLE: Final[str] = (
    "QLabel { "
    "    background-color: transparent; "
    "    color: #888888; "
    "    font-size: 14px; "
    f"    font-family: {UI_FONT_FAMILY}, sans-serif; "
    "}"
)