import os

from pytest import Config


def pytest_configure(config: Config) -> None:
    """Ensure METOFFICE_API_KEY is set before any test module is imported."""
    os.environ.setdefault("METOFFICE_API_KEY", "test-key")


# Register shared plugins/fixtures for the whole test tree.
# (pytest requires `pytest_plugins` to live in the top-level conftest only.)
pytest_plugins = [
    "pytestqt",
    "test.test_data.metoffice_sitespecific_point_daily.model",
]
