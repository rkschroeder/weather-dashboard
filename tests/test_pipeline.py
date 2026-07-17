from unittest.mock import MagicMock, call, patch

import pytest

from weather_dashboard.pipeline import FetchError, run_pipeline
from tests.conftest import SAMPLE_API_PAYLOAD


HOURLY_ROWS = [("2099-01-01T00:00", 10.0, 9.0, 0.0, 10.0, 5.0, 180.0, 80.0, 1.0, 30.0)]
DAILY_ROWS  = [("2099-01-01", 15.0, 5.0, 0.5, 20.0, 10.0, 270.0, "2099-01-01T07:00", "2099-01-01T17:00")]


@patch("weather_dashboard.pipeline.upsert_weather")
@patch("weather_dashboard.pipeline.parse_weather")
@patch("weather_dashboard.pipeline.fetch_weather")
@patch("weather_dashboard.pipeline.init_db")
def test_run_pipeline_calls_etl_in_order(mock_init, mock_fetch, mock_parse, mock_upsert):
    mock_fetch.return_value = SAMPLE_API_PAYLOAD
    mock_parse.return_value = (HOURLY_ROWS, DAILY_ROWS, 3600)

    run_pipeline(52.5, 13.4, label="Berlin")

    mock_init.assert_called_once()
    mock_fetch.assert_called_once_with(52.5, 13.4)
    mock_parse.assert_called_once_with(SAMPLE_API_PAYLOAD)
    mock_upsert.assert_called_once_with(
        HOURLY_ROWS, DAILY_ROWS, lat=52.5, lon=13.4, label="Berlin", utc_offset_seconds=3600
    )


@patch("weather_dashboard.pipeline.upsert_weather")
@patch("weather_dashboard.pipeline.parse_weather")
@patch("weather_dashboard.pipeline.fetch_weather")
@patch("weather_dashboard.pipeline.init_db")
def test_run_pipeline_default_label_is_empty(mock_init, mock_fetch, mock_parse, mock_upsert):
    mock_fetch.return_value = SAMPLE_API_PAYLOAD
    mock_parse.return_value = (HOURLY_ROWS, DAILY_ROWS, 3600)

    run_pipeline(52.5, 13.4)

    mock_upsert.assert_called_once_with(
        HOURLY_ROWS, DAILY_ROWS, lat=52.5, lon=13.4, label="", utc_offset_seconds=3600
    )


@patch("weather_dashboard.pipeline.fetch_weather")
@patch("weather_dashboard.pipeline.init_db")
def test_run_pipeline_propagates_fetch_error(mock_init, mock_fetch):
    mock_fetch.side_effect = FetchError("network down")

    with pytest.raises(FetchError, match="network down"):
        run_pipeline(52.5, 13.4)