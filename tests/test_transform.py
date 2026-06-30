import copy
import pytest
from tests.conftest import SAMPLE_API_PAYLOAD
from weather_dashboard.pipeline.transform import parse_weather


def test_parse_weather_returns_correct_row_counts():
    hourly_rows, daily_rows = parse_weather(SAMPLE_API_PAYLOAD)
    assert len(hourly_rows) == 2
    assert len(daily_rows) == 2


def test_parse_weather_hourly_field_order():
    hourly_rows, _ = parse_weather(SAMPLE_API_PAYLOAD)
    row = hourly_rows[0]
    h = SAMPLE_API_PAYLOAD["hourly"]
    assert row == (
        h["time"][0],
        h["temperature_2m"][0],
        h["apparent_temperature"][0],
        h["precipitation"][0],
        h["precipitation_probability"][0],
        h["windspeed_10m"][0],
        h["winddirection_10m"][0],
        h["relativehumidity_2m"][0],
        h["uv_index"][0],
        h["cloudcover"][0],
    )


def test_parse_weather_daily_field_order():
    _, daily_rows = parse_weather(SAMPLE_API_PAYLOAD)
    row = daily_rows[0]
    d = SAMPLE_API_PAYLOAD["daily"]
    assert row == (
        d["time"][0],
        d["temperature_2m_max"][0],
        d["temperature_2m_min"][0],
        d["precipitation_sum"][0],
        d["precipitation_probability_max"][0],
        d["windspeed_10m_max"][0],
        d["winddirection_10m_dominant"][0],
        d["sunrise"][0],
        d["sunset"][0],
    )


def test_parse_weather_empty_arrays():
    payload = copy.deepcopy(SAMPLE_API_PAYLOAD)
    for key in payload["hourly"]:
        payload["hourly"][key] = []
    for key in payload["daily"]:
        payload["daily"][key] = []
    hourly_rows, daily_rows = parse_weather(payload)
    assert hourly_rows == []
    assert daily_rows == []


def test_parse_weather_missing_hourly_key_raises():
    payload = copy.deepcopy(SAMPLE_API_PAYLOAD)
    del payload["hourly"]["cloudcover"]
    with pytest.raises(ValueError, match="missing field"):
        parse_weather(payload)


def test_parse_weather_missing_daily_key_raises():
    payload = copy.deepcopy(SAMPLE_API_PAYLOAD)
    del payload["daily"]["precipitation_sum"]
    with pytest.raises(ValueError, match="missing field"):
        parse_weather(payload)


def test_parse_weather_missing_top_level_key_raises():
    with pytest.raises((ValueError, KeyError)):
        parse_weather({"hourly": SAMPLE_API_PAYLOAD["hourly"]})