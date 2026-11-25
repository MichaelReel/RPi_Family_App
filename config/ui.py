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