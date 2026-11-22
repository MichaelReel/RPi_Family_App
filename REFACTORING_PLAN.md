# Refactoring Plan — RPi_Family_App

Self-contained refactoring tasks for this PyQt6 Raspberry Pi display app, organised by the 9 agreed criteria. Every task (T*) names the file(s) it touches, the exact change, and how to verify it. Tasks are independent unless an "Interacts with" note says otherwise — read those notes before starting a task.

- **Baseline (19/11/2026):** 71/71 tests passing · Python 3.14 · uv · PyQt6 6.11 · ruff unconfigured · no mypy · 17 files not formatter-clean.
- "Verify" commands assume the project root. Use `make …` targets from §T0 (or `uv run …` directly before T0 exists).
- A task touching tests always lists them — no task may leave the suite red.

## Status — completed so far (as of 20/11/2026)

| Section | Status | Evidence |
|---|---|---|
| **T0 — Tooling & enforcement** | ✅ **DONE** (T0.1–T0.4) | ruff + mypy config in `pyproject.toml`; `Makefile` present; `ruff check .` and `ruff format --check .` clean. T0.5 (pre-commit) ⬜ skipped (optional). |
| **§7 — Remove superfluous code** | ✅ **DONE** (T7.2–T7.17) | unused imports/vars + stale comments removed, `_advance_page` shim gone, `temp/` deleted; `ruff check .` clean. ⚠️ T7.1 corrected — see below. |
| **§1 — Full type annotations** | ✅ **DONE** (T1.1–T1.19) | commit `d8b6812`; mypy clean across 47 files; `make test` 71/71. |
| §2 — Short functions | ✅ **DONE** (T2.1–T2.8) | `live_clock`, `icons`, `day_card`, `four_day_grid`, **`weather_graph`** (all 5 steps of T2.5), **`adapter`** (T2.6), **`main`** (T2.7), **`icons_demo`** (T2.8) all done |
| §3 — Blank-line separation | ⬜ not started | — |
| §4 — Name-accuracy renames | ⬜ not started | `setup_grid_data`, `init_ui`, `raw_vis` still present |
| §5 — Paths that show purpose | ⬜ not started | `domain/`, root demos, `clock/widget/` unchanged |
| §6 — Accurate READMEs | ⬜ not started | READMEs last edited in the pre-plan "ACTION_ITEMS" era |
| §8 — Config in `config/` | ⬜ not started | attempted & reverted; `config/` absent |
| §9 — UPPER_CASE / underscore privates | ✅ DONE | All internal attributes now `_private`; config constants intentionally public (T9.16) |

> **⚠️ Bug fixed that the plan would have re-introduced.** The app stopped showing its window because `main.py` was left with an unassigned `MainWindow()` — CPython garbage-collects a top-level widget nothing references, so it is destroyed before `app.exec()`. Fixed in commit `686922a` by restoring `window = MainWindow()`. **T7.1 below endorses the broken form and must not be re-applied as written.**

## T0 — Tooling & enforcement (do first) — ✅ DONE (T0.1–T0.4; T0.5 skipped)

### T0.1 — Add mypy to the dev dependencies
- **File:** `pyproject.toml` (via CLI)
- **Change:** `uv add --dev mypy`. PyQt6, marshmallow and requests all ship `py.typed` — no stub packages needed.
- **Verify:** `uv run mypy --version`

### T0.2 — Add ruff + mypy configuration
- **File:** `pyproject.toml`
- **Change:** add
  - `[tool.ruff]` — `line-length = 88` (black-compatible), `target-version = "py314"`, `src = ["."]`
  - `[tool.ruff.lint]` — `select = ["F", "I", "UP", "B", "SIM", "C4"]`; leave `E501` off (the formatter owns line length)
  - `[tool.mypy]` — `python_version = "3.14"`, `mypy_path = "."`, `disallow_untyped_defs = true`, `disallow_incomplete_defs = true`, `no_implicit_optional = true`, `warn_return_any = true`, `check_untyped_defs = true`; add an override for `pytestqt.*` (`ignore_missing_imports = true`) only if mypy reports missing stubs
- **Verify:** `uv run ruff check . && uv run mypy --version`

### T0.3 — Add a Makefile
- **File:** `Makefile` (new)
- **Change:** targets —
  - `setup`: `uv sync`
  - `lint`: `uv run ruff check .`
  - `format`: `uv run ruff format .`
  - `typecheck`: `uv run mypy lib main.py config.py demos test`
  - `test`: `QT_QPA_PLATFORM=offscreen uv run pytest test/`
  - `run`: `uv run main.py`
  - `demo-clock` / `demo-met` / `demo-icons`: `uv run python -m demos.<name>` (final form after T5.2)
  - `check`: `lint typecheck test`
  - `clean`: remove `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `__pycache__`
- **Verify:** `make -n setup lint format typecheck test check`

### T0.4 — Normalise formatting and fix all lint findings
- **Files:** whole repo
- **Change:** run `uv run ruff format .` (black-compatible), then resolve every `ruff check` finding — including the new ones surfaced by T0.2's widened rule set. Baseline findings (17× unused imports/vars F401/F841, 3× shadowed imports F811, 1× undefined `QtBot` F821) are all covered by specific §1/§7 tasks; delete anything that remains.
- **Verify:** `uv run ruff check .` and `uv run ruff format --check .` both clean; `make test` green; `uv run black --check .` still passes (both stay "compatible").

### T0.5 — (Optional) pre-commit hooks
- **File:** `.pre-commit-config.yaml` (new)
- **Change:** ruff + ruff-format + mypy hooks so the T0 gates run on commit.
- **Verify:** `uv run pre-commit run --all-files`

**Gate after T0:** `make check` (lint + typecheck + test) green.

## 1. Full type annotations — ✅ DONE (T1.1–T1.19, commit `d8b6812`)

Every function parameter, return type, local variable and instance attribute gets an explicit annotation. Enforced by mypy (T0.2). **Gate after this section:** `make typecheck` clean + `make test` green (71/71).

### T1.1 — `main.py`
- `def main() -> None`; `def __init__(self) -> None`.
- `main()` locals: `app: QApplication`, `bg_color: str`, `text_color: str`, `central_widget: QWidget`, `main_layout: QVBoxLayout`, `exit_button: QPushButton`, `weather_source: CachedWeatherSource`, `initial_report: HumanReadableWeatherReport | None`, `location_name: str | None`, `coordinates: list[Decimal] | None` (add `Decimal` + model imports).
- Interacts with T7.1: if the unused `window` var is removed, annotate nothing for it.
- **Verify:** `uv run mypy main.py`, `make test`.

### T1.2 — `lib/clock/widget/live_clock.py`
- `__init__(self, ...) -> None`; `init_ui() -> None`; `resizeEvent(self, event: QResizeEvent) -> None`; `update_clock() -> None`.
- Locals — `init_ui`: `layout: QVBoxLayout`, `day_label: QLabel`, `date_label: QLabel`, `time_label: QLabel`; `resizeEvent`: `base_height: int`, `time_font_size: int`, `sub_font_size: int`, `time_font: QFont`, `sub_font: QFont`; `update_clock`: `now: datetime`, `hours_minutes: str`, `seconds: str`, `sec_size: int`.
- Interacts with T7.16/T9.5 (`seconds_font_size` → `_seconds_font_size`).
- **Verify:** `uv run mypy lib/clock/`, `uv run pytest test/lib/clock/ -q`.

### T1.3 — `lib/metoffice/domain/schemas.py`
- All nine `make_*` methods: `data: dict[str, Any]`, `**kwargs: Any`, explicit return types (`Geometry`, `Properties`, `Feature`, `Parameters`, `Units`, `Unit`, `TimeSeries`, `Points`, `WeatherSchemaRoot`).
- `make_geometry` currently has **no return annotation** — add it.
- Interacts with T5.1 (path becomes `api/schemas.py` after the rename).
- **Verify:** `uv run mypy lib/metoffice/`, `uv run pytest test/lib/metoffice/domain/ -q`.

### T1.4 — `lib/metoffice/icons.py`
- `_IconCaches.__init__(self) -> None`.
- **Fix wrong annotation:** `load_stats_icons(self, code: int)` → `code: str` (its map is `dict[str, str]`; the `self.caches.stats_icons[code]` subscript is wrong-typed as written).
- **Verify:** `uv run mypy lib/metoffice/`, `uv run pytest test/lib/metoffice/test_icons.py -q`.

### T1.5 — `lib/metoffice/widgets/day_card.py`
- `__init__(self, parent: QWidget | None = None, config: CardStyleConfig | None = None) -> None` (current `config: CardStyleConfig = None` is an implicit-Optional trap).
- `paintEvent(self, event: QPaintEvent) -> None`; locals `opt: QStyleOption`, `p: QPainter`.
- Nested helper: `def fmt(val: Decimal | int | None, suffix: str = "") -> str` (import `Decimal`).
- `update_data` locals: `icon_pixmap: QPixmap | None`, `pixmap: QPixmap | None`.
- **Verify:** `uv run mypy lib/metoffice/widgets/`, `uv run pytest test/lib/metoffice/test_widget.py -q`.

### T1.6 — `lib/metoffice/widgets/weather_graph.py`
- `WeatherGraphWidget.__init__(self, report_source: Callable[[], HumanReadableWeatherReport | None], parent: QWidget | None = None) -> None`; locals `layout: QVBoxLayout`, `frame: _LaneFrame`, loop var `i: int`.
- `_LaneFrame.__init__(self, parent: QWidget | None = None) -> None`; attribute `self._paint_fn: Callable[[QPainter, int, int], None]` (currently an untyped class attribute).
- `_LaneFrame.paintEvent(self, event: QPaintEvent) -> None`.
- `_draw_line(..., x_pos: Callable[[datetime], float], y_pos: Callable[[float], float]) -> None`.
- `WeatherGraphWidget.paintEvent(self, event: QPaintEvent) -> None`.
- `_draw_lane` locals: `chart_left: int`, `chart_right: int`, `chart_top: int`, `chart_bottom: int`.
- `_draw_temp_lane` / `_draw_wind_lane` / `_draw_rain_uv_lane` locals: `temp_values: list[float]`, `wind_values: list[float]`, `rain_values: list[float]`, `uv_values: list[float]`.
- `_draw_date_labels` locals: `x_center: int`, `w: int`, `font: QFont`, `text_rect: QRectF`, `i: int`.
- `_draw_guides` locals: `x: int`, `f: QFont`, `i: int`.
- `_time_window` locals: `t: datetime`, `first: datetime | None`, `last: datetime | None`.
- **Verify:** `uv run mypy lib/metoffice/widgets/`, `uv run pytest test/lib/metoffice/test_weather_graph.py -q`.

### T1.7 — `icons_demo.py` (root file before T5.2, `demos/icons_demo.py` after)
- `WeatherViewerWindow.__init__(self) -> None`.
- Locals: `scroll_area: QScrollArea`, `content_widget: QWidget`, `grid_layout: QGridLayout`, `icons_dict: dict[int, QPixmap]`, `index: int`, `code: int`, `pixmap: QPixmap | None`, `scaled_pixmap: QPixmap`, `cell_widget: QWidget`, `cell_layout: QVBoxLayout`, `image_label: QLabel`, `text_label: QLabel`, `row: int`, `col: int`, `app: QApplication`, `window: WeatherViewerWindow`.
- **Verify:** `uv run mypy icons_demo.py` (or `demos/` after T5.2), import-check runs.

### T1.8 — `test/conftest.py`
- `def pytest_configure(config: Config) -> None:` using `from pytest import Config` (keeps the bare `import pytest` removable by T7.9).
- **Verify:** `uv run pytest test/ -q`.

### T1.9 — `test/lib/metoffice/conftest.py`
- Add `from pytest import Item`.
- `def pytest_runtest_setup(item: Item) -> None:` and `def pytest_runtest_teardown(item: Item, nextitem: Item | None) -> None:`.
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q` (these hooks execute there).

### T1.10 — `test/lib/clock/test_widget.py`
- `def test_widget_starts_at_fixed_time(fixed_time: datetime, mock_datetime: MagicMock, widget: LiveClockWidget) -> None:` — same parameter annotations + `-> None` on `test_widget_updates_time` (local `label: str`) and `test_widget_background_and_text_colors`.
- Interacts with T7.10: the `bg_color`/`text_color`/`seconds_color` locals are unused — delete them, do **not** annotate.
- **Verify:** `uv run pytest test/lib/clock/ -q`.

### T1.11 — `test/lib/metoffice/test_widget.py`
- **Fix undefined `QtBot` (F821):** add `from pytestqt.qtbot import QtBot` (pytest-qt ships typing; if mypy reports missing stubs add `# type: ignore[import-untyped]`).
- Annotate: `test_featured_layout_initialization(qtbot: QtBot, report_source: HumanReadableWeatherReport) -> None`; `test_grid_card_data_assignment(report_source: HumanReadableWeatherReport, grid_widget: FourDayGridWidget) -> None` (local `first_card: DayCardWidget`); `test_update_grid_data_handles_report_source_exception(qtbot: QtBot, grid_widget: FourDayGridWidget) -> None`; `test_refresh_timer_fires(qtbot: QtBot, grid_widget: FourDayGridWidget) -> None` (local `mock_source: MagicMock`); `test_graph_widget_updates(qtbot: QtBot, grid_widget: FourDayGridWidget) -> None`.
- Fix the local `expected_human_report_snapshot` fixture: `-> HumanReadableWeatherReport` and parameter `days: list[DailyForecastPoint] | None = None` (current `callable[[DailyForecastPoint, ...]]` is not a valid type).
- Replace `lambda: (_ for _ in ()).throw(RuntimeError(...))` with an explicit `def _failing_source() -> HumanReadableWeatherReport: raise RuntimeError(...)`.
- Interacts with T7.11 (unused-import cleanup in this file).
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q`.

### T1.12 — `test/lib/metoffice/test_icons.py`
- Fixtures: `def qapp(qtbot: QtBot) -> QApplication:` (import `QtBot` as in T1.11); `def mock_icon_dir(tmp_path: Path, qapp: QApplication) -> Path:`.
- `def test_weather_icon_loading(mock_icon_dir: Path) -> None:` locals `icons: dict[int, QPixmap]`, `file_path: Path`, `first: QPixmap`, `second: QPixmap`; same shape for `test_stats_icon_loading`.
- Note: these annotations make the `Path` import *used* — see the T7.12 note.
- **Verify:** `uv run pytest test/lib/metoffice/test_icons.py -q`.

### T1.13 — `test/lib/metoffice/test_client.py`
- `def test_client_calls_api_with_expected_params(mock_post: MagicMock) -> None:` locals `result: HumanReadableWeatherReport | None`, `call_kwargs: dict[str, object]`.
- `def test_connection_error_returns_empty_report(mock_post: MagicMock) -> None:` local `result: HumanReadableWeatherReport | None`.
- `def test_invalid_json_returns_empty_report(mock_post: MagicMock) -> None:` locals `result: HumanReadableWeatherReport | None`, `mock_response: MagicMock`.
- **Verify:** `uv run pytest test/lib/metoffice/test_client.py -q`.

### T1.14 — `test/lib/metoffice/domain/test_schemas.py`
- `def sample_json_data() -> dict[str, Any]:` (import `Any`).
- `def test_schema_loads_valid_json(sample_json_data: dict[str, Any]) -> None:` locals `schema: WeatherSchemaRootSchema`, `result: WeatherSchemaRoot`.
- `def test_extracted_dataclass_values(sample_json_data: dict[str, Any]) -> None:` locals `weather_obj: WeatherSchemaRoot`, `first_feature: Feature`, `first_param_dict: dict[str, Unit]`, `dynamic_key: str`, `details: Unit` (import `Feature`, `Unit`).
- `def test_schema_rejects_missing_required_fields() -> None:` locals `schema: WeatherSchemaRootSchema`, `corrupted_payload: dict[str, object]`, `exc_info: pytest.ExceptionInfo[ValidationError]`.
- Interacts with T5.1 (file moves to `test/lib/metoffice/api/` after the rename).
- **Verify:** `uv run pytest test/lib/metoffice/domain/test_schemas.py -q`.

### T1.15 — `test/lib/metoffice/test_weather_source.py`
- Annotate in each test: `source: CachedWeatherSource`, `result: HumanReadableWeatherReport | None`; where asserted: `first: HumanReadableWeatherReport`, `second: HumanReadableWeatherReport`, `fresh: HumanReadableWeatherReport`, `stale: HumanReadableWeatherReport`, `report: HumanReadableWeatherReport`, `cached: HumanReadableWeatherReport`.
- Interacts with T7.15 (unused `timedelta` import — delete, it stays unused).
- **Verify:** `uv run pytest test/lib/metoffice/test_weather_source.py -q`.

### T1.16 — `test/lib/widgets/test_swapping_container.py`
- Annotate every `qtbot` parameter as `QtBot` (import as in T1.11).
- Locals per test: `page1: QLabel`, `page2: QLabel`, `page: QLabel`, `pages: list[QLabel]`, `container: SwappingContainerWidget`.
- **Verify:** `uv run pytest test/lib/widgets/ -q`.

### T1.17 — `test/lib/metoffice/test_weather_graph.py`
- Annotate every `qtbot` parameter as `QtBot` (import as in T1.11).
- Locals: `report: HumanReadableWeatherReport`, `widget: WeatherGraphWidget`, `days: list[DailyForecastPoint]`; in the series tests `result`/value locals as `list[float]`.
- `_make_days` / `_make_report` / `_make_hourly` / `_make_three_hourly` are already fully annotated — leave them alone.
- **Verify:** `uv run pytest test/lib/metoffice/test_weather_graph.py -q`.

### T1.18 — `test/lib/metoffice/test_adapter.py` and `test/lib/test_packages.py`
- `test_adapter.py`: already fully annotated — run mypy to confirm and add anything it flags.
- `test_packages.py`: add `-> None` to both `test_…` functions.
- **Verify:** `uv run mypy test/`, `uv run pytest test/lib/ -q`.

### T1.19 — `clock_demo.py` and `met_demo.py`
- Both are already fully annotated (including `clock_demo` locals) — verify with mypy only and annotate anything it flags.
- **Verify:** `uv run mypy clock_demo.py met_demo.py` (or `demos/` after T5.2).

**Gate after §1:** `make typecheck` clean, `make test` 71/71.

## 2. Short functions, single responsibility — ✅ DONE (T2.1–T2.8)

Extract cohesive private `_` methods; the public API of widgets/modules stays unchanged unless a task says otherwise. Target: no function over ~40 lines. **Gate:** `make test` green + import-check `uv run python -c "import main"`.

### T2.1 — `lib/clock/widget/live_clock.py` — ✅ DONE
- `init_ui()` (~40 lines) → `self._build_labels()`, `self._build_layout()`, `self._start_timer()`.
- `resizeEvent()` (~28) → `self._compute_font_sizes(base_height: int) -> tuple[int, int, int]` + apply the fonts in `resizeEvent`.
- **Verify:** `uv run pytest test/lib/clock/ -q`. ✅ test green, ruff/format/mypy clean.

### T2.2 — `lib/metoffice/icons.py` — ✅ DONE
- Extracted the duplicated load loop into a module-level `_load_icons[T](code_to_filename: Mapping[T, str], icon_dir: Path) -> dict[T, QPixmap]` (PEP 695 type param; handles filename dedup + missing-file logging).
- `load_weather_icons` / `load_stats_icons` are now thin wrappers that delegate to `_load_icons` (preserves the `_IconCaches` singleton + `invalidate_caches` contract the tests use — so the plan's `_load_icon_range(range(40), …)` shape was rejected as it would have broken `test_icons.py`).
- **Verify:** `uv run pytest test/lib/metoffice/ -q`. ✅ 54 passed, ruff check + format clean, mypy clean.

### T2.3 — `lib/metoffice/widgets/day_card.py` — ✅ DONE
- `__init__` (~85) → `self._initialise_icon_caches()`, `self._build_main_labels()`, `self._build_metric_labels()`, `self._apply_metric_alignments()`, `self._build_layout()` (the nested `create_metric_row` became `self._build_metric_row`).
- `update_data` (~50) → `self._apply_style()`, `self._apply_texts(data)`, `self._apply_icons(data)`; the nested `fmt` helper became `self._fmt` and the inline weather-icon block became `self._set_weather_icon`.
- Interacts with T9.6 (private renames) — T9.6 already DONE, so this pass is clean.
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q`. ✅ 11 passed; ruff check + format + mypy clean; no method over 28 lines.

### T2.4 — `lib/metoffice/widgets/four_day_grid.py` — ✅ DONE
- `__init__` (~50) → `self._build_featured_config()`, `self._build_secondary_config()`, `self._build_layouts()`, `self._start_refresh_timer()`.
- `setup_grid_data()` (~30) → `self._fetch_report_for_setup()` (keeps the `RuntimeError` the tests assert), `self._create_cards()`, `self._attach_cards_to_layouts()`.
- Public API unchanged: `setup_grid_data` / `update_grid_data` still callable (T4.8 rename not yet applied).
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q`. ✅ 11 passed; ruff check + format + mypy clean.

### T2.5 — `lib/metoffice/widgets/weather_graph.py` — ✅ DONE (all 5 steps)

**Completed (21/11/2026):**
- ✅ **Step 1** — `__init__` (~40) → `self._build_title() -> QLabel` (line 135) + `self._build_lanes() -> list[_LaneFrame]` (line 145).
- ✅ **Step 2** — `_time_window` (~30, line 260) → one-line dispatcher + `_window_from_fine_data()` (line 273) / `_window_from_days()` (line 286) / `_fallback_window()` (line 296).
- ✅ **Step 3** — `_draw_lane` (~90, line 320) → `_draw_lane_frame()` (line 349) + `_draw_lane_axis_label()` (line 411) + `_draw_lane_series()` (line 428) + `_draw_lane_icons()` (line 457).
- ✅ **Step 4** — Lane painting split into dispatcher + data helpers:
  - `_paint_temp_lane` (line 582) → `_paint_temp_lane_data` (line 592)
  - `_paint_wind_lane` (line 691) → `_paint_wind_lane_data` (line 701)
  - `_paint_rain_uv_lane` (line 765) → `_paint_rain_uv_lane_data` (line 775)
  - Also fixed pre-existing F821 `NameError`s in the Step-4 helpers: signatures referenced undefined `Hourly`/`ThreeHourly` → corrected to `HourlyForecastPoint`/`ThreeHourlyForecastPoint`.
- ✅ **Step 5** — `_draw_line` (~40, line 545) → dispatcher `_draw_line` (line 545) + `_draw_line_segments(painter, pts, color)` (line 569) + `_draw_line_dots(painter, pts, color)` (line 586). Both helpers are `@staticmethod` and are invoked as `WeatherGraphWidget._draw_line_*` from within the dispatcher (the only caller of `_draw_line` is `_draw_lane_series`, line 456, so no further call sites needed updating).

**Verify (all steps):** `uv run pytest test/lib/metoffice/test_weather_graph.py -q`. ✅ 13 passed; `ruff check` clean; `mypy` clean (also fixed `_window_from_fine_data` tuple-unpack `attr-defined` errors and the optional-list argument mismatch at the `_continuous_series` call sites via `hourly or []` / `three_hourly or []`).

### T2.6 — `lib/metoffice/adapter.py` — ✅ DONE
- ✅ Extracted the three duplicated per-entry mapping loops into focused `@staticmethod` helpers: `_map_daily_entry(entry, model_run_at) -> DailyForecastPoint`, `_map_hourly_entry(entry, model_run_at) -> HourlyForecastPoint`, `_map_three_hourly_entry(entry, model_run_at) -> ThreeHourlyForecastPoint`. Each `_to_*_report` is now a thin loop (list comprehension) over `feature.properties.time_series`.
- ✅ Added a shared module-level `_parse_time(raw_time, model_run_at) -> datetime` helper to unify the `fromisoformat(...replace("Z", "+00:00"))` + fallback logic that was duplicated 3× (daily/hourly/three-hourly).
- Note: the plan's `_parse_model_run_date(root)` step was superseded — the model-run-date parse is already a single shared expression in each `_to_*_report` (no `root.parameters[0]` access exists in the current code), so the real duplication was the per-entry mapping + time-parse, which is now unified.
- **Verify:** `uv run pytest test/lib/metoffice/test_adapter.py -q`. ✅ 8 passed; full suite 71/71; `ruff check` clean; `mypy` clean.

### T2.7 — `main.py` — ✅ DONE
- ✅ `MainWindow.__init__` (~65) → `self._build_clock_section(hour_minutes_color, seconds_color, day_color, date_color) -> LiveClockWidget`, `self._build_weather_section(bg_color) -> SwappingContainerWidget`, `self._add_exit_button() -> QPushButton`. `__init__` is now a thin ~35-line orchestrator (window title, central widget, layout, colours, stylesheet, addWidget calls, showFullScreen).
- ✅ Moved the `from config import WEATHER_SWAP_MS` import from inside `__init__` to the top of the module (it was a local import; now a module-level import used by `_build_weather_section`).
- ✅ The `self._weather_group` / `self._weather_graph` instance attributes were dropped — they were only used to build the `SwappingContainerWidget` page list, so the two widgets are now local to `_build_weather_section` (the container holds them). `self._weather_container` is retained.
- T8.2 interaction: the 5 colour strings are kept local (passed into the build methods) — they will move to `config/ui.py` in T8.2, so no colour extraction was done here (annotate first, extract second).
- **Verify:** `make check` green (ruff + mypy + 71/71 tests); `uv run python -c "import main"` OK.

### T2.8 — `icons_demo.py` (root before T5.2, `demos/` after) — ✅ DONE
- ✅ `WeatherViewerWindow.__init__` (~55) → `self._build_scroll_area() -> QScrollArea` and `self._build_icon_cell(code: int, pixmap: QPixmap) -> QWidget`. `__init__` is now a thin ~18-line orchestrator (window title, resize, scroll area, icon load, grid loop).
- ✅ Added the `from PyQt6.QtGui import QPixmap` import needed to annotate `_build_icon_cell`'s parameter/return.
- **Verify:** `uv run ruff check icons_demo.py` clean; `uv run mypy icons_demo.py` clean; `uv run python -c "import icons_demo"` OK; full suite 71/71.

**Gate after §2:** `make check` green; public surface of all widgets unchanged (tests prove it).

## 3. Blank lines between logical sections in long functions — ⬜ not started

Apply **after §2**, to the functions that legitimately stay long. Rule: one blank line between logical blocks (setup → compute → apply / fetch → map → return). **Gate:** `make test` green (purely formatting).

### T3.1 — `lib/metoffice/adapter.py`
- In `_to_daily_report`'s loop body: blank between (time parse) / (weather code + condition) / (visibility) / (point construction).

### T3.2 — `lib/metoffice/widgets/weather_graph.py`
- `_draw_lane`: grid → labels → clip → series. `_refresh`: error path → success path. The `_paint_*`/`_draw_*_lane` methods: fine data → daily fallback.

### T3.3 — `lib/metoffice/widgets/day_card.py`
- `update_data` (or its §2-split parts): style → text → icons.

### T3.4 — `lib/metoffice/icons.py`
- In `_load_icon_range`: iterate → file-exists check → cache-store.

### T3.5 — `main.py`
- `MainWindow.__init__`: window → layout → colours → clock → weather → button → show.

### T3.6 — `lib/clock/widget/live_clock.py`
- `resizeEvent`: scale-compute → font-build → apply.
- **Verify (all §3):** `make test` green.

## 4. Names that correctly represent purpose — ⬜ not started

### T4.1 — `clock_demo.py` (root before T5.2)
- `widget_window` → `clock_widget` (it's a `LiveClockWidget`, not a window).
- **Verify:** import-check the demo.

### T4.2 — `met_demo.py` (root before T5.2)
- `widget_window` → `grid_widget`.
- Window title `"8-Day Reflow Weather Grid Tracker"` → `"4-Day Weather Grid (demo)"` (it builds a 4-day grid).
- **Verify:** import-check the demo.

### T4.3 — `lib/metoffice/widgets/weather_graph.py`
- `self.setTitle("7-Day Forecast")` → `"8-Day Forecast"` (the graph draws days 1–7 **plus** an 8th-day label; tests build 8-day reports).
- Module docstring line 3: "7-day forecast" → "8-day forecast".
- **Verify:** `uv run pytest test/lib/metoffice/test_weather_graph.py -q`.

### T4.4 — `lib/metoffice/adapter.py`
- Loop local `w_code` → `raw_weather_code`; `raw_vis` → `raw_visibility`.
- **Verify:** `uv run pytest test/lib/metoffice/test_adapter.py -q`.

### T4.5 — `lib/metoffice/icons.py`
- Per-call local `pixmap_cache` → `code_to_pixmap` (the shared cache `loaded_icons` keeps its name — it's accurate).
- **Verify:** `uv run pytest test/lib/metoffice/test_icons.py -q`.

### T4.6 — `test/lib/metoffice/test_client.py`
- Docstrings: `"should return None"` → `"should return an empty report"` on both error tests (they assert `is not None` — the code is right, the docstrings are wrong).
- **Verify:** `uv run pytest test/lib/metoffice/test_client.py -q`.

### T4.7 — `lib/clock/widget/live_clock.py`
- `init_ui()` (public, but only called internally) → `_build_ui()`.
- **Verify:** `uv run pytest test/lib/clock/ -q`.

### T4.8 — `lib/metoffice/widgets/four_day_grid.py`
- `setup_grid_data()` → `_initialise_cards()`; `update_grid_data()` → `_refresh_cards()`.
- Update the call site in `met_demo.py` (`grid.setup_grid_data()` → `grid._initialise_cards()`).
- `report_source` stays **public** — it's the DI seam tests and demos assign to (note it in the class docstring).
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q`, import-check the demo.

## 5. Logical structure; paths that show purpose — ⬜ not started

### T5.1 — Rename `lib/metoffice/domain/` → `lib/metoffice/api/`
- **Why:** it holds the **wire-format contract** (marshmallow schemas + raw API models), and the name `domain` collides with `lib/metoffice/models.py` (the app-facing models) — two `models.py` in one tree.
- **Change:**
  - `git mv lib/metoffice/domain lib/metoffice/api` (create the target dir first if needed)
  - `git mv test/lib/metoffice/domain test/lib/metoffice/api`
  - Update imports: `lib/metoffice/adapter.py` (`lib.metoffice.domain.models` → `lib.metoffice.api.models`), `test/lib/metoffice/api/test_schemas.py` (`domain.schemas` → `api.schemas`), `test/lib/metoffice/test_adapter.py` (`domain.models` → `api.models`)
  - Update docstrings that say "domain models" → "API models" (`adapter.py`, `api/schemas.py`, `api/models.py`)
- **Alternative (if rejected):** keep `domain/` and rename `lib/metoffice/models.py` → `lib/metoffice/report.py` instead.
- **Verify:** `uv run pytest test/ -q` (71/71), `uv run mypy lib test`.

### T5.2 — Move root demos into a `demos/` package
- `mkdir demos && git mv clock_demo.py met_demo.py icons_demo.py demos/ && touch demos/__init__.py`.
- Run as modules from the root so `lib…` imports resolve: `uv run python -m demos.clock_demo` (Makefile targets already use this form).
- Update READMEs that reference the old paths (T6.1).
- **Verify:** `uv run python -c "import demos.clock_demo, demos.met_demo, demos.icons_demo"` from the root; `make test`.

### T5.3 — Unify `lib/clock/widget/` → `lib/clock/widgets/`
- `git mv lib/clock/widget lib/clock/widgets`.
- Update imports: `demos/clock_demo.py`, `test/lib/clock/test_widget.py`.
- (Convention: shared widgets live in `lib/widgets/`, feature widgets in `lib/<feature>/widgets/`.)
- **Verify:** `uv run pytest test/lib/clock/ -q`, import-check the demo.

### T5.4 — `lib/metoffice/icons/weather/spares/` — **keep**
- **Decision:** this is an unused-but-intentional local asset folder (manual icon-swap workflow, git-ignored). Document it in the icons README (T6.4) rather than deleting.
- **Verify:** none (no code change); `git status` stays clean.

## 6. Accurate READMEs with complete steps — ⬜ not started

Do this **last** — after T0.3/T5.2 — so the documented commands match reality.

### T6.1 — Rewrite root `README.md`
Current problems: "weekly Weather panel" (wrong — it's a 4-day card grid **and** an 8-day stats graph that auto-swap), missing demo/test/dev commands, typos ("depencies", "can be retrieve", "an new terminal").
New structure:
1. **What it is** — full-screen Raspberry Pi display: live clock + weather area that auto-swaps every 5 min (`WEATHER_SWAP_MS`) between the 4-day card grid and the 8-day temperature/wind/rain/UV graph; click to swap immediately.
2. **Requirements** — Raspberry Pi 4/5, 64-bit Raspberry Pi OS (or any Linux desktop).
3. **Setup & run** — `git clone`, `uv sync`, `uv run main.py` (or `make setup && make run`).
4. **Configuration** — table: `METOFFICE_API_KEY` (required), `METOFFICE_LATITUDE` (default `54.3`), `METOFFICE_LONGITUDE` (default `-7.3`) — sourced from `config/metoffice.py`.
5. **Demos** — `make demo-clock` / `demo-met` / `demo-icons` (or `uv run python -m demos.…`).
6. **Development** — `make lint`, `make typecheck`, `make test`, `make check`, `make format`.
7. **Raspberry Pi without uv** — install uv, then `uv pip install -r pyproject.toml`, `python3 main.py`.
- **Verify:** run every command in the new README once.

### T6.2 — Refresh `REPOSITORY_GUIDE.md`
Specific fixes:
- Directory tree: add missing files — `lib/metoffice/weather_source.py`, `widgets/weather_graph.py`, `widgets/weather_group.py`, `widgets/location_label.py`, `lib/widgets/swapping_container.py`, `test/lib/metoffice/test_client.py`, `test_weather_graph.py`, `test_weather_source.py`, `test/lib/widgets/test_swapping_container.py`, `test/test_data/metoffice_sitespecific_point_threehourly/`.
- **Wrong claim:** "client.py (missing) — No tests" → `test_client.py` exists (3 tests).
- Weather UI description: now grid + graph + `SwappingContainerWidget` (not "4-day forecast only").
- "Build & Run": drop the redundant `uv pip install pyqt6` after `uv sync`.
- "Current Test Coverage" table: refresh to actual counts (71 tests across 10 test modules).
- Add sections: Makefile targets (T0.3), tooling (ruff + mypy, T0.2), demos (T5.2).
- Reflect the `api/` rename if T5.1 was done.
- **Verify:** every path in the tree exists (`find lib test demos -name '*.py'`), every claim cross-checked against the code.

### T6.3 — Slim `lib/metoffice/README.md`
- Remove the env-var prose duplicated from the root README.
- Keep: module contents, where the API key comes from, pointer to the root README for setup.
- **Verify:** no factual drift vs `config/metoffice.py`.

### T6.4 — Trim `lib/metoffice/icons/weather/README.md`
- Remove "alerting icons must for now be downloaded from the NRK GitHub page" (not shipped here).
- Keep Yr attribution + MIT license.
- Add one line explaining `spares/` (see T5.4).
- **Verify:** folder contents match the description (`ls` the icon dirs).

### T6.5 — `pyproject.toml`
- `description = "Add your description here"` → `"A PyQt6 Raspberry Pi display app: live clock + Met Office weather forecast with auto-swapping views."`
- **Verify (all §6):** grep the READMEs for old paths (`clock_demo.py` at root, `domain/`) — none remain.

## 7. Remove superfluous code — ✅ DONE (T7.2–T7.17; T7.1 corrected — see below)

**Gate:** `uv run ruff check .` clean + `make test` green (71/71).

### T7.1 — `main.py` — ⚠️ DO NOT APPLY THE "inline" STEP (superseded by fix `686922a`)
- Delete commented-out line `# self.resize(400, 600)`. — ✅ done
- ~~`window = MainWindow()` → inline `MainWindow()` (F841 unused var)~~ — **WRONG — do not do this.** That local is *not* dead code: it is the only reference keeping the top-level `QMainWindow` alive. Inlining it lets CPython garbage-collect the window before `app.exec()` runs, so **no window appears** (bug reported 20/11/2026, fixed in `686922a`).
- **Correct form (already in place):** `window = MainWindow()  # noqa: F841  # reference must outlive app.exec()`.
- **Verify:** `make run` shows the window; `ruff check main.py` clean (the noqa suppresses the false-positive F841); `make test` green.

### T7.2 — `met_demo.py` (root before T5.2)
- Remove `import requests` (F401 — never used).
- Remove stale comment `# Might replace these 2 lines with something better once we have a better layout system`.
- **Verify:** `uv run ruff check met_demo.py`, import-check the demo.

### T7.3 — `icons_demo.py` (root before T5.2)
- Remove unused `import sys`, `Path` and `QPixmap` imports (F401).
- **Verify:** `uv run ruff check icons_demo.py`, import-check the demo.

### T7.4 — `clock_demo.py` (root before T5.2)
- Remove unused `seconds_color` local (F841) — do **not** annotate it (see T1.10 note).
- **Verify:** `uv run ruff check clock_demo.py`, import-check the demo.

### T7.5 — `lib/metoffice/adapter.py`
- Remove unused `TimeSeries` import (F401).
- **Verify:** `uv run ruff check lib/metoffice/adapter.py`, `uv run pytest test/lib/metoffice/test_adapter.py -q`.

### T7.6 — `lib/widgets/swapping_container.py`
- Remove the deprecated `_advance_page` shim (kept only for backward compat; used only by tests).
- Update `test/lib/widgets/test_swapping_container.py`: 3 call sites `_advance_page()` → `_swap_page()`.
- **Verify:** `uv run pytest test/lib/widgets/ -q`.

### T7.7 — `lib/metoffice/icons.py`
- Remove the two `# Optional: loaded_icons[code] = pixmap_cache[code]` commented-out blocks.
- **Verify:** `make test` (pure deletion).

### T7.8 — Defensive `getattr` against own typed models
- `lib/metoffice/widgets/weather_graph.py`: `getattr(report, "forecast_three_hourly", [])` → `report.forecast_three_hourly`.
- `lib/metoffice/widgets/day_card.py`: `getattr(data, "weather_code", None)` → `data.weather_code`.
- **Verify:** `uv run pytest test/lib/metoffice/test_weather_graph.py test/lib/metoffice/test_widget.py -q`.

### T7.9 — `test/conftest.py`
- Remove unused `import pytest` (after T1.8 switches to `from pytest import Config`).
- **Verify:** `uv run pytest test/ -q`.

### T7.10 — `test/lib/clock/test_widget.py`
- Remove unused `import pytest` and the `Qt` import.
- Remove unused `bg_color`, `text_color`, `seconds_color` locals (see T1.10/T7.4).
- **Verify:** `uv run ruff check test/`, `uv run pytest test/lib/clock/ -q`.

### T7.11 — `test/lib/metoffice/test_widget.py`
- Remove unused top-level `expected_human_report_snapshot` import (F811 shadowing), and the unused `datetime`, `timedelta`, `Decimal`, `QSize`, `QResizeEvent`, `DailyForecastPoint`, `DayCardWidget` imports.
- Fix undefined `qtbot: QtBot` with `from pytestqt.qtbot import QtBot` (F821) — **prerequisite** for T1.11's annotations.
- (The obscure `lambda: (_ for _ in ()).throw(...)` replacement is T1.11's job.)
- **Verify:** `uv run ruff check test/`, `uv run pytest test/lib/metoffice/test_widget.py -q`.

### T7.12 — `test/lib/metoffice/test_icons.py`
- Remove stale comment `# Assuming your code is inside weather_loader.py`.
- Note: the `Path` import is **not** dead once T1.12 annotates `tmp_path: Path` — do not remove it.
- **Verify:** `uv run pytest test/lib/metoffice/test_icons.py -q`.

### T7.13 — `test/lib/metoffice/domain/test_schemas.py`
- Remove comment `# Import your classes and schemas from your module`.
- **Verify:** `uv run pytest test/lib/metoffice/domain/test_schemas.py -q` (or `api/` after T5.1).

### T7.14 — `test/lib/metoffice/test_adapter.py`
- Remove unused `expected_human_report_snapshot` import.
- **Verify:** `uv run ruff check test/`, `uv run pytest test/lib/metoffice/test_adapter.py -q`.

### T7.15 — `test/lib/metoffice/test_weather_source.py`
- Remove unused `timedelta` import.
- **Verify:** `uv run ruff check test/`, `uv run pytest test/lib/metoffice/test_weather_source.py -q`.

### T7.16 — `lib/clock/widget/live_clock.py`
- Remove the `getattr(self, "seconds_font_size", 34)` startup hack: initialise `self._seconds_font_size: int = 34` in `__init__` (final name after T9.5) and read it directly in `update_clock`.
- **Verify:** `uv run pytest test/lib/clock/ -q`.

### T7.17 — Misc
- Delete the empty `temp/` directory (`rmdir temp`).
- Optional: `make clean` to drop the stale root `__pycache__/`.
- **Verify (all §7):** `uv run ruff check .` clean, `make test` 71/71.

## 8. Config in `config/` — ⬜ not started (attempted & reverted)

New layout:

```
config/
├── __init__.py    # re-exports so `from config import X` keeps working
├── metoffice.py   # today's config.py contents (API URL/headers/params, refresh intervals)
└── ui.py          # colours, fonts, card styles, graph palette, label styles
```

In-file `_UPPERCASE: Final` stays for tuning constants unlikely to change (margins, ratios, `HTTP_TIMEOUT`) — per the agreed rule. **Gate:** `make check` green + each demo still renders.

### T8.1 — Create the `config/` package
- `mkdir config && git mv config.py config/metoffice.py`.
- Create `config/ui.py` (populated by T8.2–T8.8).
- `config/__init__.py`: explicitly re-export all public names so existing `from config import MET_REFRESH_MS` etc. keeps working everywhere (client, weather_source, tests, demos).
- **Verify:** `make test`, `uv run mypy config/ main.py lib/`.

### T8.2 — `main.py` colours → `config/ui.py`
- `APP_BG_COLOR = "#000022"`, `APP_TEXT_COLOR = "#0000aa"`, `CLOCK_LABEL_COLOR = "#0000aa"`, `CLOCK_DAY_DATE_COLOR = "#0000FF"`, `CLOCK_SECONDS_COLOR = "#000088"`.
- `main.py` imports them (replaces the 5 local colour strings).
- **Verify:** `make test`, run the app briefly (`make run`) to confirm colours unchanged.

### T8.3 — Shared font family
- `UI_FONT_FAMILY = "Arial"` in `config/ui.py`.
- Use in `live_clock.py`, `day_card.py` (`"Arial, sans-serif"` → `f"{UI_FONT_FAMILY}, sans-serif"`), `weather_graph.py`, `location_label.py`.
- `live_clock` font ratios/min-sizes/margins and `weather_graph` layout tuning (margins, dot sizes, thresholds, font px) stay **in-file** as `_UPPERCASE: Final[int]`.
- **Verify:** `make test`, visual check via a demo.

### T8.4 — Card style dataclasses → `config/ui.py`
- Move `UIElementStyle` and `CardStyleConfig` (and their default values) from `day_card.py` to `config/ui.py` — config must stay a leaf module, so the dataclasses move with the values.
- `day_card.py`: `from config.ui import CardStyleConfig` + re-export it so `from lib.metoffice.widgets.day_card import CardStyleConfig` (used by `test_widget.py`) still works.
- Add a `DEFAULT_DAY_CARD_STYLE: CardStyleConfig` instance in `config/ui.py`.
- **Verify:** `make test`, `uv run mypy lib/ test/`.

### T8.5 — `four_day_grid.py` style configs → `config/ui.py`
- `FEATURED_DAY_CARD_STYLE: CardStyleConfig` (the current 9 magic values: 400/38/12/10 px text, 56/80/38 px icon box, `#007bff` border) and `SECONDARY_DAY_CARD_STYLE: CardStyleConfig` (10/8/7/6 px text, 56 px box, `#555555` border) in `config/ui.py`.
- `DAY_GRID_SPACING: Final[int] = 10`.
- `four_day_grid.py` imports them; delete the two inline `CardStyleConfig(...)` blocks.
- Interacts with T9.7 (`feature_config`/`secondary_config` attributes disappear or become private).
- **Verify:** `make test`, `uv run mypy lib/`.

### T8.6 — `weather_graph.py` palette → `config/ui.py`
- `GRAPH_TEMP_MAX_COLOR`, `GRAPH_TEMP_MIN_COLOR`, `GRAPH_WIND_COLOR`, `GRAPH_RAIN_COLOR`, `GRAPH_UV_COLOR`, `GRAPH_LABEL_COLOR`, `GRIDLINE_COLOR`, `MAJORGRIDLINE_COLOR`, `MINORGRIDLINE_COLOR` (as `Final[str]`).
- `weather_graph.py` imports them; delete the module-level colour block.
- **Verify:** `make test`, visual check via `make demo-met`.

### T8.7 — `location_label.py`
- `_DEFAULT_STYLE: CardStyleConfig` → `LOCATION_LABEL_STYLE: CardStyleConfig` in `config/ui.py`; import it.
- **Verify:** `make test`.

### T8.8 — Duplicated `bg_color` default
- `swapping_container.py`, `weather_group.py`, `four_day_grid.py`, `weather_graph.py`: `bg_color: str = "#000022"` → `bg_color: str = APP_BG_COLOR` (import from `config`).
- **Verify:** `make test`, `uv run mypy lib/`.

### T8.9 — `icons_demo.py`
- `ICON_SIZE: Final[int] = 64`, `ICON_GRID_COLUMNS: Final[int] = 4`, `ICON_GRID_SPACING: Final[int] = 20` in-file (T9.12 folds the `max_columns` local into `ICON_GRID_COLUMNS`).
- **Verify:** `uv run pytest test/ -q` (not covered by tests — visual check via `make demo-icons`).

### T8.10 — `config/metoffice.py`
- `WEATHER_SWAP_MS`, `MET_REFRESH_MS`, `MET_*` constants stay as-is (already correct UPPER_CASE public config). `client.py`'s `HTTP_TIMEOUT` stays in-file (renamed by T9.1).
- **Verify (all §8):** `make check` green, plus run each demo once to confirm visuals are unchanged.

## 9. UPPER_CASE constants and underscore-prefixed privates — ✅ DONE (T9.1–T9.16)

**Gate:** mypy + tests green after **each** rename (mypy catches broken references).

### T9.1 — `lib/metoffice/client.py` — ✅ done
- `HTTP_TIMEOUT` → `_HTTP_TIMEOUT` (private constant, used only in this module).
- **Verify:** `uv run pytest test/lib/metoffice/test_client.py -q`, `uv run mypy lib/metoffice/client.py`.

### T9.2 — `lib/metoffice/adapter.py` — ✅ done
- `WEATHER_CODE_MAP` → `_WEATHER_CODE_MAP`.
- **Verify:** `uv run pytest test/lib/metoffice/test_adapter.py -q`.

### T9.3 — `lib/metoffice/icons.py` — ✅ done
- `caches` → `_caches`. Update internal uses (3 sites) + `test/lib/metoffice/conftest.py` (1 site: `caches.weather_icons = {}`) + `test/lib/metoffice/test_icons.py` (4 sites).
- **Verify:** `uv run pytest test/lib/metoffice/ -q`.

### T9.4 — `lib/metoffice/widgets/weather_graph.py` — ✅ done
- _LaneFrame_ and all module-level constants are already `_`-prefixed (privacy satisfied). The `Final` typing on the palette constants is T8.6's job in §8 (deferred).
- **Verify:** mypy clean.

### T9.5 — `lib/clock/widget/live_clock.py` — ✅ done
- `time_label` / `day_label` / `date_label` / `timer` → `_time_label` / `_day_label` / `_date_label` / `_timer`.
- `seconds_font_size` → `_seconds_font_size` (initialised in `__init__` per T7.16).
- Update `test/lib/clock/test_widget.py` (uses `widget.day_label`, `widget.date_label`, `widget.time_label`).
- **Verify:** `uv run pytest test/lib/clock/ -q`.

### T9.6 — `lib/metoffice/widgets/day_card.py` — ✅ done
- `self.config` → `self._style_config`.
- `self.lbl_*` → `self._label_*`: `_label_date`, `_label_icon`, `_label_cond`, `_label_temp_high`, `_label_temp_low`, `_label_wind`, `_label_feels`, `_label_rain`, `_label_uv`.
- `self.ico_*` → `self._icon_*`: `_icon_temp_high`, `_icon_temp_low`, `_icon_wind`, `_icon_feels`, `_icon_rain`, `_icon_uv`.
- Updated `test/lib/metoffice/test_widget.py` (`first_card._label_temp_high`, `_label_temp_low`, `_label_cond`, `_label_rain`).
- _Note: the original plan listed `snow`/`visibility` attributes that do not exist in the current code — renamed what is actually present._
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q`.

### T9.7 — `lib/metoffice/widgets/four_day_grid.py` — ✅ done
- `cards` → `_cards`, `main_layout` → `_main_layout`, `secondary_layout` → `_secondary_layout`, `refresh_timer` → `_refresh_timer`, `report` → `_report`, `feature_config` → `_featured_config`, `secondary_config` → `_secondary_config` (or removed by T8.5).
- **`report_source` stays public** (DI seam — tests assign to it).
- Update `test/lib/metoffice/test_widget.py` accordingly (`grid_widget.cards`, `main_layout`, `secondary_layout`, `refresh_timer`).
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q`.

### T9.8 — `lib/widgets/swapping_container.py` — ✅ done
- `self.stacked` → `self._stacked` (`_swap_timer`, `_page_count` already private).
- Update `test/lib/widgets/test_swapping_container.py` (all `container.stacked` references).
- **Verify:** `uv run pytest test/lib/widgets/ -q`.

### T9.9 — `lib/metoffice/widgets/location_label.py` — ✅ done
- `self.label` → `self._label`. Update `test/lib/metoffice/test_widget.py` (`widget.label`).
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q`.

### T9.10 — `lib/metoffice/widgets/weather_group.py` — ✅ done
- `location_widget` → `_location_widget`, `grid_widget` → `_grid_widget` (no external references — confirm with `grep -rn "weather_group\." lib/ demos/ test/`).
- **Verify:** `make test`.

### T9.11 — `main.py` — ✅ done
- `main_layout`, `clock_widget`, `weather_group`, `weather_graph`, `weather_container` → `_`-prefixed (no external references).
- **Verify:** `make test`, `uv run python -c "import main"`.

### T9.12 — `icons_demo.py` (root before T5.2) — ✅ done
- Loop local `max_columns` → module-level `ICON_GRID_COLUMNS: Final[int] = 4` (shared with T8.9).
- **Verify:** import-check the demo.

### T9.13 — (Optional, cross-file) camelCase wire-model fields → snake_case — ✅ done
- _Applied against `domain/` (T5.1 not yet run). Renamed in `domain/models.py`, `domain/schemas.py` (with `data_key`), `adapter.py` (7 sites), and `test_schemas.py` + `test_adapter.py`; JSON wire keys in fixtures left camelCase._
- `api/models.py` (or `domain/models.py` if T5.1 was rejected): `modelRunDate` → `model_run_date`, `requestPointDistance` → `request_point_distance`, `timeSeries` → `time_series`.
- `api/schemas.py`: rename the schema fields and add `data_key="modelRunDate"`, `data_key="requestPointDistance"`, `data_key="timeSeries"` so JSON (de)serialisation is unchanged.
- `adapter.py`: `feature.properties.modelRunDate` → `.model_run_date` (3 sites).
- `test/lib/metoffice/api/test_schemas.py`: `first_feature.properties.modelRunDate` → `.model_run_date`.
- **Trade-off:** camelCase is defensible as an API wire contract; this task makes the code PEP8 at the cost of the `data_key` indirection.
- **Verify:** full `make test` + mypy.

### T9.14 — `lib/metoffice/widgets/weather_graph.py` (minor) — ✅ done
- `unit == "C"` string comparisons → in-file `_TEMP_UNIT: Final[str] = "C"`.
- **Verify:** `uv run pytest test/lib/metoffice/test_weather_graph.py -q`.

### T9.15 — `lib/metoffice/widgets/four_day_grid.py` (minor) — ✅ done
- `for i, data_point in enumerate(...)` → `for index, data_point in enumerate(...)` (2 sites).
- **Verify:** `uv run pytest test/lib/metoffice/test_widget.py -q`.

### T9.16 — `config/metoffice.py` — ✅ done (no change)
- **No change:** `MET_*` / `WEATHER_SWAP_MS` / `MET_REFRESH_MS` are intentionally public UPPER_CASE config — recorded decision. (Currently in `config.py`; moves to `config/` in §8/T8.1.)

## Execution order

1. **T0** — tooling/enforcement (gates for everything else)
2. **§7** — dead code (shrinks every later task)
3. **§1** — types (mypy green from here on)
4. **§9** — naming/privacy (mypy catches broken references)
5. **§2** — function splitting
6. **§3** — blank-line separation
7. **§4** — name-accuracy renames
8. **§5** — structural moves
9. **§8** — config extraction
10. **§6** — docs (last, so they match the final layout)

After **every** section: `make check` (lint + typecheck + 71/71 tests) must be green.

## Appendix — Decisions & alternatives (flag any you disagree with)

| # | Decision | Alternative |
|---|----------|-------------|
| A1 | ruff format as canonical formatter (black-compatible; black stays in dev deps) | black as canonical, ruff lint-only |
| A2 | mypy added for type enforcement | types by convention + ruff ANN rules only |
| A3 | `lib/metoffice/domain/` → `lib/metoffice/api/` | rename `lib/metoffice/models.py` → `report.py` instead |
| A4 | demos → `demos/` package (run via `python -m demos.X`) | keep root-level scripts |
| A5 | camelCase wire fields → snake_case + marshmallow `data_key` | keep camelCase as API contract |
| A6 | `icons/weather/spares/` kept + documented in icons README | delete |