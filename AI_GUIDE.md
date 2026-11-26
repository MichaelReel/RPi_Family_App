# AI / Agent Coding Style Guide

> **Purpose:** This document provides coding conventions and project-specific rules for AI agents (and human developers) working on the `RPi_Family_App` codebase. Follow these rules to keep the codebase consistent, type-safe, and testable.

---

## Type Hints

- **Every function** must have explicit parameter and return type annotations. No exceptions — not even for `__init__` (use `-> None`).
- **Use `TypeVar`** for generic functions that operate on multiple related types. Example: `_filter_recent` in `weather_graph.py` uses `_T = TypeVar("_T", HourlyForecastPoint, ThreeHourlyForecastPoint)` with `Sequence[_T]` input and `list[_T]` output.
- **Use `Sequence`** (from `collections.abc`) for read-only input parameters, `list` for mutable outputs.
- **No implicit `Optional`** — always write `X | None` explicitly.
- **No untyped defs** — mypy is configured with `disallow_untyped_defs = true` and `disallow_incomplete_defs = true`.
- **Annotate local variables** in complex functions where the type is not obvious from the assignment.
- **Use `Final`** for module-level constants that should not be reassigned.

## Naming Conventions

- **Private methods/attributes:** prefix with `_` (e.g. `_filter_recent`, `_build_lanes`, `_days`).
- **Public API:** no underscore prefix. Public methods are the ones called from outside the class (e.g. `report_source`, `update_data`).
- **Constants:** `UPPER_CASE` (e.g. `MET_REFRESH_MS`, `GRAPH_TEMP_MAX_COLOR`).
- **Config constants** in `config/` are intentionally public (no underscore) — they are the public configuration surface.
- **In-file tuning constants** (margins, ratios, font sizes) use `_UPPER_CASE: Final[int]` — private to the module.
- **Test helpers:** `_make_*` prefix (e.g. `_make_days`, `_make_hourly`, `_make_report`).
- **Test functions:** `test_*` prefix, descriptive of the behaviour being verified.

## Test Patterns

### Framework
- **pytest** with **pytest-qt** for Qt widget testing.
- **freezegun** for deterministic time-based testing.
- `--import-mode=importlib` and `pythonpath = ["."]` are set in `pyproject.toml`.

### Time-Based Tests
- Tests that depend on `datetime.now()` **must** use `freezegun.freeze_time` to pin the clock.
- Test data helpers use `2026-11-25` as the base date.
- When constructing widget instances with fine-grained data (hourly/three-hourly), wrap the test body in `freeze_time("2026-11-25 12:00:00")` so the data is "recent" relative to the frozen clock.
- Example:
  ```python
  def test_widget_with_fine_data(qtbot: QtBot) -> None:
      with freeze_time("2026-11-25 12:00:00"):
          days = _make_days(8)
          hourly = _make_hourly([(0, 10, 6, 12, 8)])
          report = _make_report(days, hourly=hourly)
          widget = WeatherGraphWidget(report_source=lambda: report)
          qtbot.addWidget(widget)
          widget.show()
          assert len(widget._hourly) == 1
  ```

### Qt Widget Tests
- Always call `qtbot.addWidget(widget)` to register the widget for cleanup.
- Call `widget.show()` before asserting on rendered state.
- Use `widget.grab()` or `frame.render(pixmap)` to force a paint cycle when testing visual output.
- For pixel-level assertions, use a tolerance (`tol = 12`) to account for antialiasing.

### Test Data
- Use the shared test data in `test/test_data/` for API response snapshots.
- Build test reports with the `_make_report` helper (accepts `days`, `hourly`, `three_hourly`).
- Build individual forecast points with `_make_hourly`, `_make_three_hourly`, `_make_days` helpers.

### Test Structure
- One behaviour per test function.
- Docstrings should describe **what** is being verified and **why** (include regression context where relevant).
- Arrange → Act → Assert pattern.
- No test should depend on execution order.

## Code Structure

### Function Length
- Target: no function over ~40 lines.
- Extract cohesive private `_` methods for logical blocks (setup → compute → apply).
- Use blank lines between logical sections within long functions.

### Module Structure
- **`config/`** — global configuration (API URLs, UI styling, constants). Leaf module — no imports from `lib/`.
- **`lib/`** — application logic (widgets, adapters, clients, models).
- **`demos/`** — standalone demo scripts.
- **`test/`** — mirrors the `lib/` structure.

### Dependency Injection
- Widgets accept a `report_source: Callable[[], HumanReadableWeatherReport | None]` for data fetching.
- This enables testing with mock data and decoupling from the HTTP client.

## Linting & Formatting

- **Ruff** — linting and formatting (configured in `pyproject.toml`).
  - `line-length = 88` (black-compatible)
  - `target-version = "py311"`
  - Rules: `F`, `I`, `UP`, `B`, `SIM`, `C4`
- **mypy** — static type checking (strict mode).
  - `disallow_untyped_defs = true`
  - `disallow_incomplete_defs = true`
  - `no_implicit_optional = true`
  - `warn_return_any = true`
  - `check_untyped_defs = true`

## Running Checks

```bash
make lint        # ruff check .
make format      # ruff format .
make typecheck   # mypy lib main.py config demos/... test
make test        # QT_QPA_PLATFORM=offscreen uv run pytest test/
make check       # lint + typecheck + test
```

## Project-Specific Rules

1. **Never inline `window = MainWindow()`** in `main.py` — the local reference keeps the top-level `QMainWindow` alive. Inlining it lets CPython garbage-collect the window before `app.exec()`.
2. **Forecast day skipping:** The grid widget displays days 1-4 (not day 0), treating "today" as already passed.
3. **`_filter_recent`** drops fine-grained points older than 24h before "now" — this anchors the graph's left edge to the current time.
4. **Config constants** in `config/` are intentionally public (no underscore prefix).
5. **In-file tuning constants** use `_UPPER_CASE: Final[int]` — private to the module.
6. **`report_source`** stays public on `FourDayGridWidget` — it's the DI seam tests and demos assign to.
7. **`lib/metoffice/icons/weather/spares/`** is git-ignored — unused-but-intentional local asset folder.

## Git Conventions

- **One commit per task** — each logical change gets its own commit.
- **Single-line commit messages** — use one concise line (no multi-line body).
- **Never push** — pushing is the user's job; the agent only commits locally.
- **Update `REPOSITORY_GUIDE.md`** in the same commit as the changes it documents.

## Language-Specific Rules

- **Python:** follow `~/.ai-rules-python.md` for Python-specific conventions.
- **Shell:** use `bash` (not `fish`) for agent commands.
- **Dates:** use UK date format (DD/MM/YYYY) in documentation and comments.