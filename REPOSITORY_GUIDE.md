# RPi Family App Repository Guide

> **Purpose:** This document provides a structured overview of the `RPi_Family_App` codebase for LLM agents and developers. It covers architecture, module responsibilities, data flow, configuration, and testing conventions.

---

## Project Overview

A full-screen PyQt6 application designed for Raspberry Pi + Touch Screen displays. The app shows:
1. A **live clock** widget (hours, minutes, seconds)
2. A **weather area** sourced from the UK Met Office DataHub API that auto-swaps every 5 minutes (`WEATHER_SWAP_MS`) between a **4-day forecast card grid** and an **8-day stats graph** (temperature, rain, UV, wind). Clicking the weather area swaps immediately.

### Entry Points

| File | Purpose |
|------|---------|
| `main.py` | Main application — full-screen window with clock + weather grid |
| `demos/met_demo.py` | Standalone weather widget demo (resizable window) |
| `demos/clock_demo.py` | Standalone clock widget demo |
| `demos/icons_demo.py` | Icon loading demo |

### Configuration

**`config/`** defines global constants (Met Office API config in `config/metoffice.py`, UI styling in `config/ui.py`):
- `MET_DAILY_URL` — Met Office DataHub API endpoint (daily forecast)
- `MET_HOURLY_URL` — Met Office DataHub API endpoint (1-hourly forecast, used by the graph)
- `MET_THREE_HOURLY_URL` — Met Office DataHub API endpoint (3-hourly forecast, used by the graph)
- `MET_HEADERS` — HTTP headers (includes API key from `METOFFICE_API_KEY` env var)
- `MET_PARAMS` — Query parameters (latitude/longitude from env vars)
- `MET_REFRESH_MS` — Millisecond interval for weather data refresh timer (1 hour)
- `WEATHER_SWAP_MS` — Millisecond interval for auto-swapping between the weather grid and graph (5 minutes)

**Environment variables:**
- `METOFFICE_API_KEY` — **required** (Met Office DataHub API key)
- `METOFFICE_LATITUDE` — optional, default `54.3`
- `METOFFICE_LONGITUDE` — optional, default `-7.3`

---

## Architecture

### Directory Structure

```
RPi_Family_App/
├── config/                          # Global configuration package
│   ├── __init__.py                  # Re-exports so `from config import X` keeps working
│   ├── metoffice.py                 # Met Office API URLs, headers, params, refresh intervals
│   └── ui.py                        # UI styling (colours, fonts, card styles, graph palette)
├── main.py                          # Main app entry point (PyQt6 full-screen window)
├── demos/
│   ├── met_demo.py                  # Standalone weather widget demo
│   ├── clock_demo.py                # Standalone clock widget demo
│   └── icons_demo.py                # Icon loading demo
├── lib/
│   ├── clock/widgets/live_clock.py  # Live clock PyQt6 widget
│   ├── widgets/swapping_container.py  # Generic auto-swapping page container
│   └── metoffice/
│       ├── client.py                # HTTP client for Met Office API
│       ├── adapter.py               # Domain adapter: raw schema → human-readable models
│       ├── models.py                # Human-readable weather dataclasses
│       ├── icons.py                 # Icon loading (weather + stats PNG icons)
│       ├── weather_source.py        # TTL-cached weather source (shared by widgets)
│       ├── api/
│       │   ├── models.py            # Strongly-typed API models (Marshmallow dataclasses)
│       │   └── schemas.py           # Marshmallow schemas for JSON deserialization
│       └── widgets/
│           ├── day_card.py          # Individual day card widget
│           ├── four_day_grid.py     # 4-day grid layout widget
│           ├── location_label.py    # Location name + coordinates label
│           ├── weather_group.py     # Groups location label + 4-day grid
│           └── weather_graph.py     # 8-day multi-lane stats graph
└── test/
    ├── lib/clock/test_widget.py     # Clock widget tests
    ├── lib/metoffice/
    │   ├── api/test_schemas.py      # Marshmallow schema tests
    │   ├── test_adapter.py          # Adapter transformation tests
    │   ├── test_client.py           # HTTP client tests (mocked)
    │   ├── test_icons.py            # Icon loading tests
    │   ├── test_weather_graph.py    # Weather graph widget tests
    │   ├── test_weather_source.py   # Cached weather source tests
    │   └── test_widget.py           # Weather widget tests
    ├── lib/widgets/test_swapping_container.py  # Swapping container tests
    ├── lib/test_packages.py         # Package import tests
    └── test_data/
        ├── metoffice_sitespecific_point_daily/
        │   ├── domain.json          # Sample Met Office API JSON response
        │   └── model.py             # Expected snapshot fixture
        └── metoffice_sitespecific_point_threehourly/
            └── domain.json          # Sample 3-hourly API JSON response
```
---

## Data Flow

```
Met Office API (HTTP JSON)
        │
        ▼
┌──────────────┐
│  client.py   │  requests.get() → response.json()
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ api/schemas.py  │  WeatherSchemaRootSchema().load() — Marshmallow deserialization
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ api/models.py   │  WeatherSchemaRoot, Feature, Properties, TimeSeries, etc.
└──────┬───────────┘
       │
       ▼
┌────────────────┐
│  adapter.py    │  MetOfficeAdapter.to_human_readable() — transforms domain models
└──────┬─────────┘
       │
       ▼
┌──────────────────────┐
│  models.py           │  HumanReadableWeatherReport, DailyForecastPoint (dataclasses)
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ weather_source.py    │  CachedWeatherSource — TTL cache so the API is hit once per refresh
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ weather_group.py     │  WeatherGroupWidget — location label + FourDayGridWidget
│ weather_graph.py     │  WeatherGraphWidget — 8-day multi-lane stats chart
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ swapping_container.py│  SwappingContainerWidget — auto-swaps the two pages (WEATHER_SWAP_MS)
└──────────────────────┘
```

---

## Module Responsibilities

### `lib/metoffice/client.py`
- Makes HTTP GET request to Met Office DataHub API
- Deserializes JSON response using `WeatherSchemaRootSchema`
- Transforms domain models via `MetOfficeAdapter`
- Returns `HumanReadableWeatherReport | None`
- **Error handling:** catches network exceptions and non-200 HTTP status codes

### `lib/metoffice/api/schemas.py`
- Marshmallow schemas for deserializing Met Office API JSON
- Schema hierarchy: `WeatherSchemaRootSchema` → `FeatureSchema` → `PropertiesSchema` → `TimeSeriesSchema`
- `TimeSeriesSchema` uses `unknown = INCLUDE` to accept dynamic/arbitrary keys
- `parameters` field maps dynamic `{key: ParameterDetails}` structure as list of dicts

### `lib/metoffice/api/models.py`
- Strongly-typed dataclasses representing the Met Office API structure
- Key classes: `WeatherSchemaRoot`, `Feature`, `Properties`, `TimeSeries`, `Geometry`, `Location`, `ParameterDetails`, `Unit`, `Symbol`
- `TimeSeries.data` captures arbitrary key-value pairs from the API's dynamic time-series structure

### `lib/metoffice/adapter.py`
- `MetOfficeAdapter.to_human_readable()` — the core transformation pipeline
- Maps raw `WeatherSchemaRoot` → `HumanReadableWeatherReport`
- Translates Met Office weather codes (integers) to human-readable condition strings via `WEATHER_CODE_MAP`
- Extracts day/night values for temperature, rain/snow probability, wind, visibility, UV index
- Converts decimal/string values to `Decimal` and `int` as needed

### `lib/metoffice/models.py`
- `DailyForecastPoint` — single day's forecast with 12+ fields (date, temps, wind, rain, UV, etc.)
- `HumanReadableWeatherReport` — top-level report with location, coordinates, model run time, and list of `DailyForecastPoint`

### `lib/metoffice/icons.py`
- `MET_OFFICE_ICON_MAP` — maps weather codes (0-30) to PNG filenames
- `MET_OFFICE_STATS_MAP` — maps stat names to icon filenames
- `load_weather_icons(directory_path)` — loads weather PNG icons into `{code: QPixmap}` dict
- `load_stats_icons(directory_path)` — loads stat PNG icons into `{name: QPixmap}` dict
- Both functions have internal caching to prevent duplicate `QPixmap` creation

### `lib/metoffice/widgets/day_card.py`
- `DayCardWidget` — renders a single day's weather forecast
- Uses `CardStyleConfig` and `UIElementStyle` dataclasses for theme configuration
- Class-level `_icon_cache` and `_stats_cache` for shared icon memory
- `update_data()` method refreshes label text and icons without rebuilding layout

### `lib/metoffice/widgets/four_day_grid.py`
- `FourDayGridWidget` — displays 4 forecast days in a featured + secondary layout
- Day 1 (featured): large card, top row, stretch=2
- Days 2-4 (secondary): smaller cards, bottom row, horizontal layout
- `report_source: Callable[[], HumanReadableWeatherReport]` — injected function for data fetching
- Background `QTimer` refreshes data every `MET_REFRESH_MS` milliseconds
- **Note:** Skips forecast day 0 (today), displays days 1-4

### `lib/metoffice/widgets/location_label.py`
- `LocationLabelWidget` — displays the location name and coordinates (from the report)

### `lib/metoffice/widgets/weather_group.py`
- `WeatherGroupWidget` — groups the location label and the 4-day grid into a single widget
- Used as one page of the `SwappingContainerWidget`

### `lib/metoffice/widgets/weather_graph.py`
- `WeatherGraphWidget` — renders an 8-day multi-lane stats chart
- Lanes (top to bottom): temperature (min/max/feels-like), rain probability + UV index, wind (avg + gust)
- Built from the dense 1-hourly and 3-hourly forecast points

### `lib/metoffice/weather_source.py`
- `CachedWeatherSource` — TTL-cached wrapper around `get_human_readable_weather()`
- Shared by both weather widgets so the Met Office API is hit at most once per `MET_REFRESH_MS`

### `lib/widgets/swapping_container.py`
- `SwappingContainerWidget` — generic container that periodically cycles through a list of widgets
- Uses a `QStackedWidget` + `QTimer`; clicking anywhere swaps to the next page immediately
- Every page change (timer or click) restarts the swap timer

### `lib/clock/widgets/live_clock.py`
- `LiveClockWidget` — live clock with configurable colors and optional day/date display
- `update_clock()` method updates time labels with HTML-formatted seconds in smaller font
- Background `QTimer` updates every second

---

## Testing Conventions

### Test Framework
- **pytest** with **pytest-qt** for Qt widget testing
- `--import-mode=importlib` (from `pyproject.toml`)
- `pythonpath = ["."]` — root directory on import path

### Test Data
- `test/test_data/metoffice_sitespecific_point_daily/domain.json` — real Met Office API response snapshot
- `test/test_data/metoffice_sitespecific_point_daily/model.py` — `expected_human_report_snapshot` pytest fixture

### Current Test Coverage
71 tests across 10 test modules:

| Module | Test File | Tests |
|--------|-----------|-------|
| `clock/widgets/live_clock.py` | `test/lib/clock/test_widget.py` | 1 |
| `metoffice/api/schemas.py` | `test/lib/metoffice/api/test_schemas.py` | 3 |
| `metoffice/adapter.py` | `test/lib/metoffice/test_adapter.py` | 8 |
| `metoffice/client.py` | `test/lib/metoffice/test_client.py` | 6 |
| `metoffice/icons.py` | `test/lib/metoffice/test_icons.py` | 6 |
| `metoffice/weather_source.py` | `test/lib/metoffice/test_weather_source.py` | 7 |
| `metoffice/widgets/` | `test/lib/metoffice/test_widget.py` | 11 |
| `metoffice/widgets/weather_graph.py` | `test/lib/metoffice/test_weather_graph.py` | 13 |
| `widgets/swapping_container.py` | `test/lib/widgets/test_swapping_container.py` | 9 |
| package imports | `test/lib/test_packages.py` | 7 |

### Running Tests
```bash
uv run pytest test/ -v
```

---

## Key Design Decisions

1. **Dependency Injection:** `FourDayGridWidget` accepts a `report_source` callable, enabling testing with mock data and decoupling from the HTTP client.

2. **Adapter Pattern:** `MetOfficeAdapter` cleanly separates domain deserialization (schemas) from business logic transformation (human-readable models).

3. **Configuration Dataclasses:** `CardStyleConfig` and `UIElementStyle` allow runtime theme changes without hardcoded CSS strings in widget code.

4. **Class-Level Icon Caching:** `DayCardWidget` shares `_icon_cache` and `_stats_cache` across instances to avoid redundant file I/O and `QPixmap` allocations.

5. **Forecast Day Skipping:** The grid widget displays days 1-4 (not day 0), treating "today" as already passed and showing the next 4 days.

---

## External Dependencies

| Package | Purpose |
|---------|---------|
| `PyQt6` | GUI framework (widgets, layouts, timers, painters) |
| `requests` | HTTP client for Met Office API |
| `marshmallow` | JSON schema deserialization (domain models) |

---

## Build & Run

```bash
# Setup
uv sync

# Set environment variables
export METOFFICE_API_KEY="your_key"
export METOFFICE_LATITUDE="54.3141"
export METOFFICE_LONGITUDE="-7.4058"

# Run
uv run main.py               # Full app
uv run python demos/met_demo.py     # Weather only
uv run python demos/clock_demo.py   # Clock only
uv run python demos/icons_demo.py   # Icons only

# Test
uv run pytest test/ -v
```

### Makefile targets

| Target | Command | Purpose |
|--------|---------|---------|
| `make setup` | `uv sync` | Install dependencies |
| `make run` | `uv run main.py` | Run the full app |
| `make demo-clock` | `uv run python demos/clock_demo.py` | Clock widget demo |
| `make demo-met` | `uv run python demos/met_demo.py` | Weather widget demo |
| `make demo-icons` | `uv run python demos/icons_demo.py` | Icon loading demo |
| `make lint` | `uv run ruff check .` | Lint with Ruff |
| `make format` | `uv run ruff format .` | Format with Ruff |
| `make typecheck` | `uv run mypy lib main.py config demos/... test` | Type-check with mypy |
| `make test` | `QT_QPA_PLATFORM=offscreen uv run pytest test/` | Run the test suite |
| `make check` | `lint` + `typecheck` + `test` | Full CI-style check |
| `make clean` | removes caches | Clean build/test caches |

### Tooling

- **Ruff** — linting and formatting (configured in `pyproject.toml`)
- **mypy** — static type checking (strict mode, configured in `pyproject.toml`)
- **pytest** + **pytest-qt** — test framework with Qt widget support

