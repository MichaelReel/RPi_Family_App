"""Verify that all package __init__.py files are importable."""

import importlib


def test_lib_package_importable() -> None:
    """lib/__init__.py should be importable."""
    importlib.import_module("lib")


def test_metoffice_package_importable() -> None:
    """lib/metoffice/__init__.py should be importable."""
    importlib.import_module("lib.metoffice")


def test_metoffice_api_package_importable() -> None:
    """lib/metoffice/api/__init__.py should be importable."""
    importlib.import_module("lib.metoffice.api")


def test_metoffice_widgets_package_importable() -> None:
    """lib/metoffice/widgets/__init__.py should be importable."""
    importlib.import_module("lib.metoffice.widgets")


def test_clock_package_importable() -> None:
    """lib/clock/__init__.py should be importable."""
    importlib.import_module("lib.clock")


def test_clock_widgets_package_importable() -> None:
    """lib/clock/widgets/__init__.py should be importable."""
    importlib.import_module("lib.clock.widgets")


def test_widgets_package_importable() -> None:
    """lib/widgets/__init__.py should be importable."""
    importlib.import_module("lib.widgets")
