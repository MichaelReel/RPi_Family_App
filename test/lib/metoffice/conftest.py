"""Test configuration for lib/metoffice."""
import pytest

from lib.metoffice.icons import caches


def pytest_runtest_setup(item):
    """Reset icon singleton caches before each test across all test files."""
    caches.invalidate_caches()


def pytest_runtest_teardown(item, nextitem):
    """Reset icon singleton caches after each test to prevent cross-file state leaks."""
    caches.invalidate_caches()