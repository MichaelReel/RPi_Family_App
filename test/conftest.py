import pytest

def pytest_configure(config):
    """Ensure METOFFICE_API_KEY is set before any test module is imported."""
    import os
    os.environ.setdefault("METOFFICE_API_KEY", "test-key")
