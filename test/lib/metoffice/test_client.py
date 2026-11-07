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

class TestHTTPTimeout:
    """Tests that the HTTP request uses a timeout to prevent the UI from freezing."""

    @patch("lib.metoffice.client.requests.get")
    def test_timeout_argument_passed(self, mock_get):
        """Verify that requests.get() is called with a timeout argument."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        get_human_readable_weather()
        # Assert that timeout was passed as a keyword argument
        call_kwargs = mock_get.call_args.kwargs
        assert "timeout" in call_kwargs, "requests.get() was called without a timeout"
        assert call_kwargs["timeout"] > 0, "timeout should be a positive value"

class TestClientCoverage:
    """Additional tests for client.py coverage (action item #3)."""

    @patch("lib.metoffice.client.requests.get")
    def test_json_decode_error_returns_none(self, mock_get):
        """A response with invalid JSON should be caught and return None."""
        import requests.exceptions
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value", "doc", 0
        )
        mock_get.return_value = mock_response
        result = get_human_readable_weather()
        assert result is None

    @patch("lib.metoffice.client.requests.get")
    def test_non_200_status_returns_none(self, mock_get):
        """A non-200 HTTP status code should return None."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response
        result = get_human_readable_weather()
        assert result is None

    @patch("lib.metoffice.client.MetOfficeAdapter.to_human_readable")
    @patch("lib.metoffice.client.WeatherSchemaRootSchema")
    @patch("lib.metoffice.client.requests.get")
    def test_successful_response_returns_report(
        self, mock_get, mock_schema_cls, mock_adapter
    ):
        """A successful 200 response with valid JSON should return a HumanReadableWeatherReport."""
        mock_report = MagicMock()
        mock_adapter.return_value = mock_report
        mock_schema = MagicMock()
        mock_schema.load.return_value = MagicMock()
        mock_schema_cls.return_value = mock_schema

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = get_human_readable_weather()
        assert result is not None
        assert result is mock_report
