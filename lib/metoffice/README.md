# Met Office weather module

Fetches, adapts, and renders Met Office DataHub forecasts for the family display.

## Setup

Configuration is read from environment variables (see [`config/`](../../config/)). The only required one is `METOFFICE_API_KEY` — obtain it from the [Met Office DataHub getting-started guide](https://datahub.metoffice.gov.uk/docs/getting-started). `METOFFICE_LATITUDE` and `METOFFICE_LONGITUDE` are optional (defaults `54.3` / `-7.3`).

Full setup and run instructions live in the [root README](../../README.md).

## Module contents

| Path | Purpose |
|------|---------|
| `client.py` | HTTP client for the Met Office DataHub API (daily / hourly / three-hourly endpoints). |
| `adapter.py` | Maps raw API responses into the app's typed domain models. |
| `api/` | Marshmallow schemas and wire-level dataclasses for the API payloads. |
| `models.py` | App-level domain models (e.g. `HourlyForecastPoint`). |
| `weather_source.py` | Refreshes the forecast on a timer and exposes it to the widgets. |
| `icons.py` | Loads and caches the weather / stats icon pixmaps. |
| `widgets/` | Qt widgets: `weather_group`, `weather_graph`, `day_card`, `four_day_grid`, `location_label`. |
| `icons/` | Icon assets — `weather/` (forecast codes) and `stats/` (metric glyphs). |