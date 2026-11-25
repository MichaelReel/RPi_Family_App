"""UI styling configuration (colours, fonts, card styles, graph palette).

Populated incrementally by T8.2–T8.8. Kept as a leaf module: it must not
import from ``lib`` so it can be imported by any widget without a cycle.
"""

from typing import Final

# App-wide colours (T8.2)
APP_BG_COLOR: Final[str] = "#000022"
APP_TEXT_COLOR: Final[str] = "#0000aa"
CLOCK_LABEL_COLOR: Final[str] = "#0000aa"
CLOCK_DAY_DATE_COLOR: Final[str] = "#0000FF"
CLOCK_SECONDS_COLOR: Final[str] = "#000088"