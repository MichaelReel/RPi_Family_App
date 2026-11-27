# Plan: Add Calendar + List Widget to SwappingContainerWidget

## Goal
Add a third rotating page to the `SwappingContainerWidget` in `main.py` — a **Calendar + List** composite widget (display-only, no interaction).

## Requirements (confirmed)
- **Calendar**: 7×5 grid (35 days), current week + next 4 weeks, **Sunday start**.
- **Current day**: distinct border/outline (keeps its month color).
- **Weekend cells** (Sat/Sun): distinct coloring.
- **Month-specific coloring**: a distinct background color per calendar month (e.g. Nov vs Dec differ).
- **Day numbers** shown in every cell.
- **Short month name** (e.g. "Nov") on the **first cell shown in the grid** for each month (not necessarily the 1st of the month — e.g. if the grid starts on the 25th, the first November cell shown gets the "Nov" label, and the first December cell shown gets "Dec").
- **List**: a static, hardcoded list of family events/reminders.
- **Interaction**: display-only — no tap/click actions.

## New files

### 1. `lib/calendar/__init__.py`
Empty package marker (mirrors `lib/clock/`, `lib/metoffice/`).

### 2. `lib/calendar/widgets/__init__.py`
Empty package marker.

### 3. `lib/calendar/widgets/calendar_grid.py` — `CalendarGridWidget(QWidget)`
- Builds a 7×5 `QGridLayout` of 35 day cells.
- **Start date**: the Sunday of the current week (so the current day is always in row 0).
- Each cell is a `QLabel` (or small `QWidget`) showing:
  - The day number (e.g. "25").
  - If it is the **first cell shown in the grid** for that month (i.e. the previous cell in the grid is a different month, or it's the very first cell), also the short month name (e.g. "Nov").
- **Per-month background color**: a `dict[int, str]` mapping month (1–12) → hex color.
- **Weekend coloring**: Sat/Sun cells get a distinct visual treatment (e.g. a different background shade or a left-border accent) so they're distinguishable from weekdays within the same month.
- **Current day**: a distinct border/outline (e.g. 2px solid border) while keeping its month background color.
- No interaction (no mouse handlers).
- Uses `UI_FONT_FAMILY` for fonts.

### 4. `lib/calendar/widgets/calendar_list.py` — `CalendarListWidget(QWidget)`
- A static, hardcoded list of family events/reminders.
- Data structure: a small list of `(date_str, text)` tuples or a simple dataclass, defined at module level or as a class constant.
- Rendered as a vertical list of `QLabel`s (or a single multi-line label).
- Display-only.

### 5. `lib/calendar/widgets/calendar_group.py` — `CalendarGroupWidget(QWidget)`
- Groups `CalendarGridWidget` + `CalendarListWidget` vertically in a `QVBoxLayout`.
- Mirrors the pattern of `WeatherGroupWidget` (a clean grouping so the calendar view is a single unit for the swapping container).

## Modified files

### 6. `config/ui.py`
Add calendar color/style constants (public, `Final`):
```python
# Calendar colors
CALENDAR_MONTH_COLORS: Final[dict[int, str]] = {
    1: "#1a1a3a",   # Jan
    2: "#1a2a3a",   # Feb
    3: "#1a3a2a",   # Mar
    4: "#2a3a1a",   # Apr
    5: "#3a2a1a",   # May
    6: "#3a1a2a",   # Jun
    7: "#2a1a3a",   # Jul
    8: "#1a3a3a",   # Aug
    9: "#3a3a1a",   # Sep
    10: "#3a1a1a",  # Oct
    11: "#1a1a4a",  # Nov
    12: "#2a1a1a",  # Dec
}
CALENDAR_WEEKEND_COLOR: Final[str] = "#2a2a4a"
CALENDAR_TODAY_BORDER_COLOR: Final[str] = "#FFD700"
CALENDAR_TEXT_COLOR: Final[str] = "#cccccc"
CALENDAR_MONTH_LABEL_COLOR: Final[str] = "#888888"
CALENDAR_LIST_TEXT_COLOR: Final[str] = "#cccccc"
CALENDAR_CELL_SPACING: Final[int] = 4
```
(Exact hex values are placeholders — to be finalized.)

### 7. `main.py`
- Import `CalendarGroupWidget`.
- Build it in `_build_weather_section` (or a new `_build_calendar_section` method).
- Add it as a third page in the `SwappingContainerWidget` pages list.

### 8. `REPOSITORY_GUIDE.md`
- Document the new `lib/calendar/` package (same commit as the changes).

## New test files

### 9. `test/lib/calendar/__init__.py`
### 10. `test/lib/calendar/widgets/__init__.py`

### 11. `test/lib/calendar/widgets/test_calendar_grid.py`
Using `freezegun` (base date `2026-11-25` per AI_GUIDE) + `pytest-qt`:
- Grid has 35 cells (7×5).
- First cell is the Sunday of the current week.
- Current day cell has the today border.
- Weekend cells (Sat/Sun) have weekend styling.
- Month label appears on the first cell shown in the grid for each month (not necessarily the 1st of the month).
- November and December cells have different background colors.

### 12. `test/lib/calendar/widgets/test_calendar_list.py`
- List renders the hardcoded events.
- Correct number of items.

### 13. `test/lib/calendar/widgets/test_calendar_group.py`
- Group contains both `CalendarGridWidget` and `CalendarListWidget`.

## Conventions to follow
- `_LOGGER: Final[Logger] = getLogger(__name__)` where logging is needed.
- `Final` type annotations for module-level constants.
- `UI_FONT_FAMILY` for fonts.
- `freezegun` for date-dependent tests (base `2026-11-25`).
- `pytest-qt` (`qtbot`) for widget tests.
- Run the **combined** test suite before declaring done.
- One commit per task; update `REPOSITORY_GUIDE.md` in the same commit.

## Assumptions
- The "list" is a simple vertical list of text items (event name + optional date), hardcoded.
- Weekend coloring: a distinct background shade for Sat/Sun (exact approach TBD).
- Calendar starts on the **Sunday of the current week** (not today), so the current day is always in the first row.

## Open items (to finalize)
- [ ] Exact hex color values for months, weekend, today border.
- [ ] Exact content of the hardcoded family events list.
- [ ] Weekend coloring approach (background shade vs border accent).
- [ ] Whether the list should show dates alongside event text.
