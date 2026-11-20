def pytest_configure(config):
    """Ensure METOFFICE_API_KEY is set before any test module is imported."""
    import os

    os.environ.setdefault("METOFFICE_API_KEY", "test-key")


# Register shared fixtures for the whole test tree. (pytest requires
# `pytest_plugins` to live in the top-level conftest only.)
pytest_plugins = ["test.test_data.metoffice_sitespecific_point_daily.model"]
