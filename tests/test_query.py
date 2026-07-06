import sqlite3
from contextlib import closing

import pytest

from weather_dashboard.alerts import DEFAULT_THRESHOLDS
from weather_dashboard.db import init_db
from weather_dashboard.pipeline.load import upsert_weather, save_alert_thresholds
from weather_dashboard.query import (
    load_daily,
    load_hourly,
    load_location_label,
    load_location_history,
    load_alert_thresholds,
)


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


def test_load_location_history_returns_locations(tmp_db):
    init_db()
    # Insert with explicit timestamps — datetime('now') resolves to the second,
    # making two back-to-back inserts non-deterministically ordered otherwise
    import sqlite3
    from contextlib import closing as _closing
    with _closing(sqlite3.connect(tmp_db)) as conn:
        conn.execute("INSERT INTO locations (label, lat, lon, last_fetched) VALUES (?,?,?,?)",
                     ("Berlin, Germany", 52.5, 13.4, "2024-01-01 10:00:00"))
        conn.execute("INSERT INTO locations (label, lat, lon, last_fetched) VALUES (?,?,?,?)",
                     ("Paris, France", 48.8, 2.3, "2024-01-02 10:00:00"))
        conn.commit()
    history = load_location_history()
    assert len(history) == 2
    assert history[0]["label"] == "Paris, France"  # most recent first
    assert history[1]["label"] == "Berlin, Germany"
    assert history[0]["last_fetched"] == "2024-01-02 10:00:00"
    assert {"label", "lat", "lon", "last_fetched"} == set(history[0].keys())


def test_load_location_history_empty(tmp_db):
    init_db()
    assert load_location_history() == []


def test_load_location_history_respects_limit(tmp_db):
    init_db()
    for i in range(5):
        upsert_weather(FUTURE_HOURLY, FUTURE_DAILY, lat=float(i), lon=float(i), label=f"City {i}")
    assert len(load_location_history(limit=3)) == 3


def test_load_alert_thresholds_returns_defaults_when_not_set(tmp_db):
    init_db()
    assert load_alert_thresholds() == DEFAULT_THRESHOLDS


def test_load_alert_thresholds_merges_partial_saved_config(tmp_db):
    init_db()
    save_alert_thresholds({"uv_index": 3.0})
    thresholds = load_alert_thresholds()
    assert thresholds["uv_index"] == 3.0
    assert thresholds["precipitation_sum"] == DEFAULT_THRESHOLDS["precipitation_sum"]
    assert thresholds["temp_max"] == DEFAULT_THRESHOLDS["temp_max"]


def test_load_alert_thresholds_round_trips_full_config(tmp_db):
    init_db()
    custom = {"uv_index": 5.0, "precipitation_sum": 20.0, "temp_max": 30.0}
    save_alert_thresholds(custom)
    assert load_alert_thresholds() == custom