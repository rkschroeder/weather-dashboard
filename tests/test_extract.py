from unittest.mock import MagicMock, patch
import pytest
import requests

from weather_dashboard.pipeline.extract import FetchError, geocode_city, fetch_weather
from tests.conftest import SAMPLE_API_PAYLOAD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(json_data=None, raise_for_status=None, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    if raise_for_status:
        mock.raise_for_status.side_effect = raise_for_status
    else:
        mock.raise_for_status.return_value = None
    return mock


_GEOCODE_RESULTS = {
    "results": [
        {"name": "Berlin", "latitude": 52.5, "longitude": 13.4, "admin1": "Berlin", "country": "Germany"},
        {"name": "Berlin", "latitude": 44.5, "longitude": -71.2, "admin1": "New Hampshire", "country": "United States"},
    ]
}


# ---------------------------------------------------------------------------
# geocode_city
# ---------------------------------------------------------------------------

@patch("weather_dashboard.pipeline.extract.requests.get")
def test_geocode_city_returns_location_list(mock_get):
    mock_get.return_value = _mock_response(_GEOCODE_RESULTS)
    results = geocode_city("Berlin")
    assert len(results) == 2
    assert results[0]["lat"] == 52.5
    assert results[0]["lon"] == 13.4
    assert "Berlin" in results[0]["label"]


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_geocode_city_filters_fuzzy_matches(mock_get):
    payload = {
        "results": [
            {"name": "Berlin", "latitude": 52.5, "longitude": 13.4, "admin1": "Berlin", "country": "Germany"},
            # "Berlinchen" doesn't contain "berlin" as substring... actually it does.
            # Use a name that definitely doesn't match the query "berlin"
            {"name": "Bern", "latitude": 46.9, "longitude": 7.4, "admin1": "Bern", "country": "Switzerland"},
        ]
    }
    mock_get.return_value = _mock_response(payload)
    results = geocode_city("berlin")
    assert len(results) == 1
    assert results[0]["lat"] == 52.5


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_geocode_city_no_results_raises_value_error(mock_get):
    mock_get.return_value = _mock_response({"results": None})
    with pytest.raises(ValueError, match="City not found"):
        geocode_city("Atlantis")


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_geocode_city_all_filtered_raises_value_error(mock_get):
    payload = {"results": [{"name": "Bern", "latitude": 46.9, "longitude": 7.4, "country": "Switzerland"}]}
    mock_get.return_value = _mock_response(payload)
    with pytest.raises(ValueError, match="City not found"):
        geocode_city("berlin")


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_geocode_city_network_error_raises_fetch_error(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("timeout")
    with pytest.raises(FetchError):
        geocode_city("Berlin")


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_geocode_city_http_error_raises_fetch_error(mock_get):
    mock_get.return_value = _mock_response(
        raise_for_status=requests.exceptions.HTTPError("429")
    )
    with pytest.raises(FetchError):
        geocode_city("Berlin")


# ---------------------------------------------------------------------------
# fetch_weather
# ---------------------------------------------------------------------------

@patch("weather_dashboard.pipeline.extract.requests.get")
def test_fetch_weather_returns_data(mock_get):
    mock_get.return_value = _mock_response(SAMPLE_API_PAYLOAD)
    data = fetch_weather(52.5, 13.4)
    assert "hourly" in data
    assert "daily" in data


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_fetch_weather_missing_daily_raises(mock_get):
    mock_get.return_value = _mock_response({"hourly": SAMPLE_API_PAYLOAD["hourly"]})
    with pytest.raises(ValueError, match="missing hourly or daily"):
        fetch_weather(52.5, 13.4)


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_fetch_weather_missing_hourly_raises(mock_get):
    mock_get.return_value = _mock_response({"daily": SAMPLE_API_PAYLOAD["daily"]})
    with pytest.raises(ValueError, match="missing hourly or daily"):
        fetch_weather(52.5, 13.4)


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_fetch_weather_network_error_raises_fetch_error(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("no route")
    with pytest.raises(FetchError):
        fetch_weather(52.5, 13.4)


@patch("weather_dashboard.pipeline.extract.requests.get")
def test_fetch_weather_http_error_raises_fetch_error(mock_get):
    mock_get.return_value = _mock_response(
        raise_for_status=requests.exceptions.HTTPError("500")
    )
    with pytest.raises(FetchError):
        fetch_weather(52.5, 13.4)