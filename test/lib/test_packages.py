"""Verify that all package __init__.py files are importable."""
import importlib


def test_lib_package_importable():
    """lib/__init__.py should be importable."""
    importlib.import_module("lib")


def test_metoffice_package_importable():
    """lib/metoffice/__init__.py should be importable."""
    importlib.import_module("lib.metoffice")


def test_metoffice_domain_package_importable():
    """lib/metoffice/domain/__init__.py should be importable."""
    importlib.import_module("lib.metoffice.domain")


def test_metoffice_widgets_package_importable():
    """lib/metoffice/widgets/__init__.py should be importable."""
    importlib.import_module("lib.metoffice.widgets")


def test_clock_package_importable():
    """lib/clock/__init__.py should be importable."""
    importlib.import_module("lib.clock")


def test_clock_widget_package_importable():
    """lib/clock/widget/__init__.py should be importable."""
    importlib.import_module("lib.clock.widget")
