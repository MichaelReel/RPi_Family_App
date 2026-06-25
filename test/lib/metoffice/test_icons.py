import pytest
from pathlib import Path
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication

# Assuming your code is inside weather_loader.py
from lib.metoffice.icons import load_weather_icons, MET_OFFICE_ICON_MAP


@pytest.fixture(scope="session")
def qapp():
    """Provides a persistent QApplication instance required for QPixmap operations."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_icon_dir(tmp_path, qapp):  # Added qapp here so Qt is ready before saving
    """Creates a temporary directory filled with valid, test PNG assets using QImage."""
    
    # Create a simple blank 10x10 image using native Qt structures
    blank_image = QImage(10, 10, QImage.Format.Format_ARGB32)
    blank_image.fill(0)  # Fill with transparent pixels
    
    # Generate all expected files except for code 30 (to test missing file logic)
    for code, filename in MET_OFFICE_ICON_MAP.items():
        if code == 30:
            continue  # Intentionally skip code 30
        
        file_path = tmp_path / filename
        
        # Save using Qt's internal engine to guarantee platform compatibility
        blank_image.save(str(file_path), "PNG")
        
    return tmp_path


def test_load_weather_icons_success(qapp, mock_icon_dir):
    """Verifies that valid icons are successfully loaded into QPixmaps."""
    icons = load_weather_icons(mock_icon_dir)
    
    # Assert code 0 loaded correctly
    assert 0 in icons
    assert isinstance(icons[0], QPixmap)
    assert not icons[0].isNull()  # Checks that PyQt successfully parsed the image data


def test_load_weather_icons_missing_file(qapp, mock_icon_dir, capsys):
    """Verifies that missing files are handled gracefully without crashing."""
    icons = load_weather_icons(mock_icon_dir)
    
    # Code 30 was intentionally omitted from mock_icon_dir
    assert 30 not in icons
    
    # Verify the warning message was printed out correctly
    captured = capsys.readouterr()
    assert "Warning: Missing icon file" in captured.out
    assert "30_heavyrainandthunder.png" in captured.out


def test_load_weather_icons_caching(qapp, mock_icon_dir, monkeypatch):
    """Verifies that the internal cache prevents duplicate disk/QPixmap initializations."""
    # Spy on QPixmap initialization by modifying the dictionary mapping to create a duplicate
    # Let's map code 5 and code 6 to the exact same file name to force a cache hit
    monkeypatch.setitem(MET_OFFICE_ICON_MAP, 5, "06_fog.png")
    monkeypatch.setitem(MET_OFFICE_ICON_MAP, 6, "06_fog.png")
    
    icons = load_weather_icons(mock_icon_dir)
    
    # If caching works, both keys must point to the exact same Python object memory address
    assert icons[5] is icons[6]
