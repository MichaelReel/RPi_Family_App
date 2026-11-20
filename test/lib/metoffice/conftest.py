"""Test configuration for lib/metoffice."""

from lib.metoffice.icons import caches

pytest_plugins = ["test.test_data.metoffice_sitespecific_point_daily.model"]


def pytest_runtest_setup(item):
    """Reset icon singleton caches before each test across all test files."""
    caches.invalidate_caches()


def pytest_runtest_teardown(item, nextitem):
    """Reset icon singleton caches after each test to prevent cross-file state leaks."""
    caches.invalidate_caches()
