# RPi Family App Repository Guide

> **Purpose:** This document provides a structured overview of the `RPi_Family_App` codebase for LLM agents and developers. It covers architecture, module responsibilities, data flow, configuration, and testing conventions.

---

## Project Overview

A full-screen PyQt6 application designed for Raspberry Pi + Touch Screen displays. The app shows:
1. A **live clock** widget (hours, minutes, seconds, day, date)
2. A **4-day weather forecast** widget sourced from the UK Met Office DataHub API

### Entry Points

| File | Purpose |
|------|---------|
| `main.py` | Main application — full-screen window with clock + weather grid |
| `met_demo.py` | Standalone weather widget demo (resizable window) |
| `clock_demo.py` | Standalone clock widget demo |
| `icons_demo.py` | Icon loading demo |

### Configuration

**`config.py`** defines global constants:
- `MET_DAILY_URL` — Met Office DataHub API endpoint
- `MET_HEADERS` — HTTP headers (includes API key from `METOFFICE_API_KEY` env var)
- `MET_PARAMS` — Query parameters (latitude/longitude from env vars)
- `MET_REFRESH_MS` — Millisecond interval for weather data refresh timer

**Required environment variables:**
- `METOFFICE_API_KEY`
- `METOFFICE_LATITUDE`
- `METOFFICE_LONGITUDE`

---

## Architecture

### Directory Structure

```
RPi_Family_App/
├── config.py                        # Global configuration (API URLs, headers, params, refresh intervals)
├── main.py                          # Main app entry point (PyQt6 full-screen window)
├── met_demo.py                      # Standalone weather widget demo
├── clock_demo.py                    # Standalone clock widget demo
├── icons_demo.py                    # Icon loading demo
├── lib/
│   ├── clock/widget/live_clock.py   # Live clock PyQt6 widget
│   └── metoffice/
│       ├── client.py                # HTTP client for Met Office API
│       ├── adapter.py               # Domain adapter: raw schema → human-readable models
│       ├── models.py                # Human-readable weather dataclasses
│       ├── icons.py                 # Icon loading (weather + stats PNG icons)
│       ├── domain/
│       │   ├── models.py            # Strongly-typed domain models (Marshmallow dataclasses)
│       │   └── schemas.py           # Marshmallow schemas for JSON deserialization
│       └── widgets/
│           ├── day_card.py          # Individual day card widget
│           └── four_day_grid.py     # 4-day grid layout widget
└── test/
    ├── lib/clock/test_widget.py     # Clock widget tests
    ├── lib/metoffice/
    │   ├── domain/test_schemas.py   # Marshmallow schema tests
    │   ├── test_adapter.py          # Adapter transformation tests
    │   ├── test_icons.py            # Icon loading tests
    │   └── test_widget.py           # Weather widget tests
    └── test_data/
        └── metoffice_sitespecific_point_daily/
            ├── domain.json          # Sample Met Office API JSON response
            └── model.py             # Expected snapshot fixture
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
│ domain/schemas.py │  WeatherSchemaRootSchema().load() — Marshmallow deserialization
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ domain/models.py │  WeatherSchemaRoot, Feature, Properties, TimeSeries, etc.
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
│ four_day_grid.py     │  FourDayGridWidget — receives HumanReadableWeatherReport
│                      │  Creates DayCardWidget instances, manages refresh timer
└──────┬───────────────┘
       │
       ▼
┌──────────────────┐
│   day_card.py    │  DayCardWidget — renders date, weather icon, temps, wind, rain, UV
└──────────────────┘
```

---

## Module Responsibilities

### `lib/metoffice/client.py`
- Makes HTTP GET request to Met Office DataHub API
- Deserializes JSON response using `WeatherSchemaRootSchema`
- Transforms domain models via `MetOfficeAdapter`
- Returns `HumanReadableWeatherReport | None`
- **Error handling:** catches network exceptions and non-200 HTTP status codes

### `lib/metoffice/domain/schemas.py`
- Marshmallow schemas for deserializing Met Office API JSON
- Schema hierarchy: `WeatherSchemaRootSchema` → `FeatureSchema` → `PropertiesSchema` → `TimeSeriesSchema`
- `TimeSeriesSchema` uses `unknown = INCLUDE` to accept dynamic/arbitrary keys
- `parameters` field maps dynamic `{key: ParameterDetails}` structure as list of dicts

### `lib/metoffice/domain/models.py`
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

### `lib/clock/widget/live_clock.py`
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
| Module | Test File | Coverage |
|--------|-----------|----------|
| `clock/widget/live_clock.py` | `test/lib/clock/test_widget.py` | Basic init with mocked datetime |
| `metoffice/domain/schemas.py` | `test/lib/metoffice/domain/test_schemas.py` | Valid JSON, deep attributes, missing fields |
| `metoffice/adapter.py` | `test/lib/metoffice/test_adapter.py` | Metadata, timeseries, visibility, snapshot comparison |
| `metoffice/icons.py` | `test/lib/metoffice/test_icons.py` | Load success, missing file, caching |
| `metoffice/widgets/` | `test/lib/metoffice/test_widget.py` | Card count, data mapping, timer, layout |
| `metoffice/client.py` | **(missing)** | **No tests** |

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
python -m venv .venv
source .venv/bin/activate
uv sync
uv pip install pyqt6

# Set environment variables
export METOFFICE_API_KEY="your_key"
export METOFFICE_LATITUDE="54.3141"
export METOFFICE_LONGITUDE="-7.4058"

# Run
uv run main.py          # Full app
uv run met_demo.py      # Weather only
uv run clock_demo.py    # Clock only

# Test
uv run pytest test/ -v
```

