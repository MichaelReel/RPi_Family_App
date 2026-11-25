# RPi Family App

A full-screen PyQt6 application for a Raspberry Pi + touch-screen display. It shows:

1. A **live clock** (hours, minutes, seconds).
2. A **weather area** sourced from the UK Met Office DataHub API that **auto-swaps every 5 minutes** (`WEATHER_SWAP_MS`) between:
   - a **4-day forecast card grid** (location label + featured day + 3 secondary days), and
   - an **8-day stats graph** (temperature, rain probability, UV index, and wind).

   **Click anywhere** on the weather area to swap to the other view immediately.

## Documentation

- **[REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)** — Repository overview, architecture, data flow, module responsibilities, and testing conventions (useful for LLM agents and new developers).

## Requirements

- Raspberry Pi 4/5 (or any Linux desktop)
- 64-bit Raspberry Pi OS (or any Linux distribution) with **Python 3.11+**
- [uv](https://docs.astral.sh/uv/) for dependency management

## Setup & run

```sh
git clone https://github.com/MichaelReel/RPi_Family_App.git
cd RPi_Family_App
uv sync
uv run main.py
```

Or, using the Makefile:

```sh
make setup   # uv sync
make run     # uv run main.py
```

## Configuration

The app reads its settings from environment variables (defined in [`config/`](config/)):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `METOFFICE_API_KEY` | **Yes** | — | Met Office DataHub API key. Get one via the [Met Office getting-started guide](https://datahub.metoffice.gov.uk/docs/getting-started). |
| `METOFFICE_LATITUDE` | No | `54.3` | Forecast latitude (e.g. `54.3141`). |
| `METOFFICE_LONGITUDE` | No | `-7.3` | Forecast longitude (e.g. `-7.4058`). |

Set them before running, e.g.:

```sh
export METOFFICE_API_KEY="your_key"
export METOFFICE_LATITUDE="54.3141"
export METOFFICE_LONGITUDE="-7.4058"
```

## Demos

Standalone, resizable demos of each widget (the clock and icons demos need no API key):

```sh
make demo-clock   # uv run python demos/clock_demo.py
make demo-met     # uv run python demos/met_demo.py
make demo-icons   # uv run python demos/icons_demo.py
```

## Development

```sh
make lint        # uv run ruff check .
make format      # uv run ruff format .
make typecheck   # uv run mypy lib main.py config demos/... test
make test        # QT_QPA_PLATFORM=offscreen uv run pytest test/
make check       # lint + typecheck + test
```

## Raspberry Pi without uv

> **Python version:** this app requires **Python 3.11+**. If `python3 --version` on your Pi is below 3.11, install a newer Python first.

If you can't use `uv` on the Pi, install the dependencies with pip instead:

```sh
sudo apt update
sudo apt install -y python3-pyqt6
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r pyproject.toml
python3 main.py
```
