import pytest
from unittest.mock import patch, MagicMock

from lib.metoffice.client import get_human_readable_weather

@pytest.fixture(autouse=True)
def set_api_key_env(monkeypatch):
    """Ensure METOFFICE_API_KEY is set for every test."""
    monkeypatch.setenv("METOFFICE_API_KEY", "test-key")

class TestNetworkErrorHandling:
    """Tests that network errors are caught and the function returns None."""

    @patch("lib.metoffice.client.requests.get")
    def test_connection_error_returns_none(self, mock_get):
        """A requests.exceptions.ConnectionError should be caught and return None."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        result = get_human_readable_weather()
        assert result is None

    @patch("lib.metoffice.client.requests.get")
    def test_timeout_error_returns_none(self, mock_get):
        """A requests.exceptions.Timeout should be caught and return None."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        result = get_human_readable_weather()
        assert result is None

    @patch("lib.metoffice.client.requests.get")
    def test_request_exception_returns_none(self, mock_get):
        """A generic requests.exceptions.RequestException should be caught and return None."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.RequestException("Generic error")
        result = get_human_readable_weather()
        assert result is None
