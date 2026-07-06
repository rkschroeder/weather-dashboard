import sqlite3
from contextlib import closing

import pytest

import weather_dashboard.db as db_module
from weather_dashboard.db import init_db


def _get_columns(db_path, table):
    with closing(sqlite3.connect(db_path)) as conn:
        return {col[1] for col in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def test_init_db_creates_all_tables(tmp_db):
    init_db()
    with closing(sqlite3.connect(tmp_db)) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert {"hourly", "daily", "metadata", "locations"} <= tables


def test_init_db_hourly_columns(tmp_db):
    init_db()
    cols = _get_columns(tmp_db, "hourly")
    expected = {
        "time", "temperature_2m", "apparent_temperature", "precipitation",
        "precipitation_probability", "wind_speed", "wind_direction",
        "humidity", "uv_index", "cloud_cover",
    }
    assert expected <= cols


def test_init_db_daily_columns(tmp_db):
    init_db()
    cols = _get_columns(tmp_db, "daily")
    expected = {
        "date", "temp_max", "temp_min", "precipitation_sum",
        "precipitation_probability_max", "wind_speed_max",
        "wind_direction_dominant", "sunrise", "sunset",
    }
    assert expected <= cols


def test_init_db_is_idempotent(tmp_db):
    init_db()
    db_module._db_ready = False  # force a second run
    init_db()  # should not raise
    cols = _get_columns(tmp_db, "hourly")
    assert "temperature_2m" in cols


def test_init_db_migration_adds_missing_column(tmp_db, monkeypatch):
    # Create a minimal hourly table without apparent_temperature
    with closing(sqlite3.connect(tmp_db)) as conn:
        conn.execute("CREATE TABLE hourly (time TEXT PRIMARY KEY, temperature_2m REAL)")
        conn.execute("CREATE TABLE daily (date TEXT PRIMARY KEY, temp_max REAL, temp_min REAL, precipitation_sum REAL, wind_speed_max REAL, wind_direction_dominant REAL)")
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
        conn.commit()

    monkeypatch.setattr(db_module, "_db_ready", False)
    init_db()

    cols = _get_columns(tmp_db, "hourly")
    assert "apparent_temperature" in cols
    assert "humidity" in cols
    assert "uv_index" in cols
    assert "cloud_cover" in cols
    assert "precipitation_probability" in cols


def test_init_db_locations_columns(tmp_db):
    init_db()
    cols = _get_columns(tmp_db, "locations")
    assert {"label", "lat", "lon", "last_fetched"} <= cols


def test_init_db_locations_migration_adds_last_fetched(tmp_db, monkeypatch):
    # Simulate a locations table created before last_fetched was added
    with closing(sqlite3.connect(tmp_db)) as conn:
        conn.execute("CREATE TABLE hourly (time TEXT PRIMARY KEY, temperature_2m REAL)")
        conn.execute("CREATE TABLE daily (date TEXT PRIMARY KEY, temp_max REAL)")
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("CREATE TABLE locations (label TEXT PRIMARY KEY, lat REAL, lon REAL)")
        conn.commit()

    monkeypatch.setattr(db_module, "_db_ready", False)
    init_db()

    assert "last_fetched" in _get_columns(tmp_db, "locations")