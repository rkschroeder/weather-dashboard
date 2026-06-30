import sqlite3
from contextlib import closing

import pytest

from weather_dashboard.db import init_db
from weather_dashboard.pipeline.load import upsert_weather
from weather_dashboard.query import load_daily, load_hourly, load_location_label


# Rows dated far in the future so they are always "upcoming" relative to today
FUTURE_HOURLY = [
    ("2099-01-01T00:00", 10.0, 9.0, 0.0, 10.0, 5.0, 180.0, 80.0, 1.0, 30.0),
    ("2099-01-01T01:00", 11.0, 10.0, 0.5, 20.0, 6.0, 270.0, 75.0, 2.0, 50.0),
]
FUTURE_DAILY = [
    ("2099-01-01", 15.0, 5.0, 0.5, 20.0, 10.0, 270.0, "2099-01-01T07:00", "2099-01-01T17:00"),
    ("2099-01-02", 16.0, 6.0, 0.0, 5.0,  8.0,  180.0, "2099-01-02T07:01", "2099-01-02T16:59"),
]

# Rows dated in the past — should be excluded by the query filter
PAST_HOURLY = [("2000-01-01T00:00", 5.0, 4.0, 0.0, 0.0, 1.0, 0.0, 60.0, 0.0, 10.0)]
PAST_DAILY  = [("2000-01-01", 8.0, 2.0, 0.0, 0.0, 3.0, 0.0, "2000-01-01T07:00", "2000-01-01T17:00")]


def test_load_hourly_returns_dataframe(tmp_db):
    init_db()
    upsert_weather(FUTURE_HOURLY, FUTURE_DAILY)
    df = load_hourly()
    assert list(df.columns) == [
        "time", "temperature_2m", "apparent_temperature", "precipitation",
        "precipitation_probability", "wind_speed", "wind_direction",
        "humidity", "uv_index", "cloud_cover",
    ]
    assert len(df) == 2


def test_load_hourly_excludes_past_rows(tmp_db):
    init_db()
    upsert_weather(FUTURE_HOURLY + PAST_HOURLY, FUTURE_DAILY)
    df = load_hourly()
    assert len(df) == 2
    assert all(df["time"].dt.year == 2099)


def test_load_daily_returns_dataframe(tmp_db):
    init_db()
    upsert_weather(FUTURE_HOURLY, FUTURE_DAILY)
    df = load_daily()
    assert "date" in df.columns
    assert "temp_max" in df.columns
    assert len(df) == 2


def test_load_daily_excludes_past_rows(tmp_db):
    init_db()
    upsert_weather(FUTURE_HOURLY, FUTURE_DAILY + PAST_DAILY)
    df = load_daily()
    assert len(df) == 2
    assert all(df["date"].dt.year == 2099)


def test_load_location_label_returns_stored_value(tmp_db):
    init_db()
    upsert_weather(FUTURE_HOURLY, FUTURE_DAILY, label="Tokyo, Japan")
    assert load_location_label() == "Tokyo, Japan"


def test_load_location_label_returns_empty_string_when_not_set(tmp_db):
    init_db()
    assert load_location_label() == ""