# Action Items & Known Issues

> **Last updated:** November 2026 (reviewed against live codebase)  
> **Scope:** Issues, improvements, and missing tests identified during codebase analysis.  
> This is a temporary tracking document. Items should be moved to proper issues or PRs as they're addressed.

---

## Critical Issues (P0)

### 1. Wrong Exception Type Caught in `client.py` ✅
- **File:** `lib/metoffice/client.py` (line 4)
- **Problem:** `urllib3.exceptions.HTTPError` is *never* raised by `requests.get()`. Network errors raise `requests.exceptions.RequestException` (or subclasses like `ConnectionError`, `Timeout`, etc.). All network exceptions are silently uncaught, causing the app to crash on network failure instead of returning `None`.
- **Fix:** Replace `from urllib3.exceptions import HTTPError` with `from requests.exceptions import RequestException` and catch `requests.exceptions.RequestException`.
- **Status:** Fixed in commit 94ec074. Added tests in `test/lib/metoffice/test_client.py`.

### 2. No Timeout on HTTP Requests ✅
- **File:** `lib/metoffice/client.py` (line 16)
- **Problem:** `requests.get()` is called without a `timeout` parameter. If the Met Office API hangs, the entire PyQt6 event loop blocks indefinitely, freezing the UI.
- **Fix:** Add `timeout=30` to `requests.get()`.
- **Status:** Fixed in commit 3c7066a. `HTTP_TIMEOUT=30` constant added to `client.py` and passed to `requests.get()`.

### 3. No Test Coverage for `client.py` ✅
- **File:** Missing entirely
- **Problem:** The HTTP client module (`lib/metoffice/client.py`) has **zero test coverage**. This is the most critical gap since it handles network I/O and error handling.
- **Fix:** Create `test/lib/metoffice/test_client.py` with:
  - Mock successful API response
  - Mock network errors (ConnectionError, Timeout)
  - Mock non-200 HTTP status codes
  - Mock JSON parse failures
  - Verify `None` is returned on all error paths
- **Status:** Fixed in commit a3431d6. Added 6 tests in `test/lib/metoffice/test_client.py` covering: network errors (3), timeout argument (1), non-200 status (1), successful response (1). JSON parse failure test deferred — client doesn't handle `JSONDecodeError` yet (see P1 item #5).

---

## Significant Issues (P1)

### 4. `weather_code` Can Be `None` But Type Says `int` ✅
- **File:** `lib/metoffice/models.py` (line 18) + `lib/metoffice/adapter.py` (line 47)
- **Problem:** `weather_code: int` is non-optional in `DailyForecastPoint`, but the adapter can pass `w_code` which is `None` when neither day nor night weather code is present.
- **Fix:** Change to `weather_code: int | None` and update consumers.
- **Status:** Fixed in commit 743bf29. Changed dataclass field to `int | None` and added test `test_missing_weather_code_defaults_to_unknown`.

### 5. No Error Handling for JSON Parse Failures
- **File:** `lib/metoffice/client.py` (line 25)
- **Problem:** `response.json()` can raise `requests.exceptions.JSONDecodeError` if the response body isn't valid JSON. This will crash unhandled.
- **Fix:** Wrap `response.json()` in a try/except block.

### 6. `parameters` Schema May Not Match Real API Structure ✅
- **File:** `lib/metoffice/domain/schemas.py` (lines 89-92)
- **Problem:** The `parameters` field uses `fields.List(fields.Dict(...))` but the real Met Office API may return `parameters` as a flat dict `{param_key: ParameterDetails}`. The test passes because the test fixture is structured to match the schema, not necessarily the real API.
- **Fix:** Verify against a live API response and adjust schema accordingly.
- **Status:** Verified against live API. The real API returns `parameters` as a list of length 1 (dict mapping param names to ParameterDetails), which matches the schema. No code change needed.

---

## Minor Issues & Code Smells (P2)

### 7. Class-Level Mutable Shared State in `DayCardWidget`
- **File:** `lib/metoffice/widgets/day_card.py` (lines 65-66)
- **Problem:** `_icon_cache` and `_stats_cache` are class-level `dict` attributes shared across all instances. If one instance's path context changes or the app runs multiple widgets with different icon directories, they silently interfere. No thread-safety guard.
- **Risk:** Low in current usage — only one icon directory is ever used. Downgraded from P1.

### 8. Hardcoded Icon Reuse
- **File:** `lib/metoffice/icons.py` (line 44)
- **Problem:** The feels-like temperature uses the same icon as the low temperature.
- **Action:** Verify if this is intentional or a bug.

### 9. `print()` Instead of Logging
- **Files:** `client.py`, `icons.py`, `four_day_grid.py`
- **Problem:** `print()` statements used for error logging.
- **Fix:** Replace with Python's `logging` module.

### 10. Emoji in Test Assertions
- **File:** `test/lib/metoffice/test_widget.py` (line 56)
- **Problem:** Test asserts exact emoji text. If the rendering or emoji changes, the test fails.
- **Fix:** Consider using a regex match or normalizing the assertion.

### 11. `setup_grid_data()` Does Not Catch Exceptions from `report_source()`
- **File:** `lib/metoffice/widgets/four_day_grid.py` (line 70)
- **Problem:** `self.report_source()` is called without a try/except. If the callable raises an exception (not just returns `None`), the exception propagates and crashes the widget.
- **Fix:** Wrap `report_source()` in a try/except and handle exceptions gracefully.

### 12. Broken Internal State in `_IconCaches.load_weather_icons()` and `.load_stats_icons()`
- **File:** `lib/metoffice/icons.py` (lines 91-92, 128-129)
- **Problem:** The methods assign to local variables (`_loaded_weather_icons = ...`) instead of `self._loaded_weather_icons`. The cache guard (`if self._weather_icons_loaded: return ...`) never triggers because the flag is never set on `self`. The module-level `caches` singleton works around this, but re-entering the same method on the same instance would reload icons from disk unnecessarily.
- **Fix:** Change to `self._loaded_weather_icons = loaded_icons`, `self._weather_icons_loaded = True`, etc.

---

## Minor Issues & Code Smells (P3)

### 13. Conversion Helpers Defined Inside Loop
- **File:** `lib/metoffice/adapter.py` (lines 57-61)
- **Problem:** `to_decimal()` and `to_int()` are defined inside the loop body and redefined on every iteration.
- **Fix:** Move to module-level utility functions or static methods. Downgraded from P1 — purely stylistic, no functional impact.

### 14. No `__init__.py` Test Coverage
- **Problem:** The `__init__.py` files exist but are not tested for importability.

### 15. Unused `location_name` Field
- **File:** `lib/metoffice/models.py`, `lib/metoffice/adapter.py`
- **Problem:** The `location_name` field in `HumanReadableWeatherReport` is populated by the adapter but never consumed by any UI widget.
- **Action:** Verify whether the location name should be displayed somewhere; if not, consider removing it.

### 16. `config.py` Raises at Module Import Time
- **File:** `config.py` (line 8)
- **Problem:** `ValueError` is raised at module-level if `METOFFICE_API_KEY` is not set. Any test that imports `config.py` must have the environment variable set, or the entire test session crashes.
- **Fix:** Consider deferring validation (lazy loading) or providing a test-friendly default/override.

### 17. `pyqt6` Listed in Both `pyproject.toml` and README as a Separate Install
- **Problem:** `pyproject.toml` already lists `pyqt6` in dependencies, but the README instructs users to run `uv pip install pyqt6` separately. The separate install is redundant.
- **Fix:** Remove `pyqt6` from the README's separate install step.

---

## Missing Test Coverage Summary

| Module | Test File | Status |
|--------|-----------|--------|
| `metoffice/client.py` | `test/lib/metoffice/test_client.py` | ✅ **Covered** (6 tests) |
| `clock/widget/live_clock.py` | `test/lib/clock/test_widget.py` | Minimal — only init test |
| `config.py` | Missing | No tests |
| `main.py` | Missing | No integration tests |
| End-to-end pipeline | Missing | No integration tests |

### Recommended New Tests

1. **`test/lib/metoffice/test_client.py`** — HTTP client tests (see P0 item #3)
2. **Clock widget:** Add tests for color customization, `include_day=False`, `include_date=False`, timer behavior
3. **`config.py`:** Test env var validation and default values
4. **Integration test:** API call → schema → adapter → widget rendering (with mocked HTTP)
5. **Edge cases:** Handle empty forecast days, missing weather codes, API returning fewer than 5 days
6. **`icons.py` internal state:** Test that `_IconCaches` caching flags work correctly (exposes bug in item #12)

---

## Structural Improvement Suggestions

| # | Suggestion | Files | Priority |
|---|------------|-------|----------|
| S1 | Add retry logic to `client.py` | `client.py` | P2 |
| S2 | Extract conversion helpers from `adapter.py` | `adapter.py` | P2 |
| S3 | Replace `print()` with `logging` | Multiple | P2 |
| S4 | Dependency injection for weather client | `main.py`, `client.py` | P3 |
| S5 | Complete type hints | `client.py`, `icons.py` | P3 |
| S6 | Separate API credentials from `config.py` | `config.py` | P2 |

---

## Priority Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 3 | Wrong exception type, no timeout, no client tests |
| P1 | 3 | Optional weather_code, JSON errors, schema mismatch |
| P2 | 6 | Shared state, icon reuse, logging, emoji tests, setup_grid_data exceptions, icon cache bug |
| P3 | 7 | Loop helpers, init coverage, unused field, config import-time error, pyqt6 redundancy, S2/S4/S5 |

---

## Review Notes (November 2026)

- **Dropped:** Original item #12 ("`load_weather_icons()` Call May Be Missing Argument") — the functions have default arguments for `directory_path`, so calls without arguments are correct.
- **Downgraded:** Original #4 (class-level shared state) from P1 → P2, because the risk is low with the current single-directory usage. Original #8 (loop-defined helpers) from P1 → P3, because it's purely stylistic with no functional impact.
- **Added:** Items #11, #12, #15, #16, #17 were not previously tracked.

