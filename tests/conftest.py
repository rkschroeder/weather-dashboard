import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import pytest

import weather_dashboard.db as db_module


SAMPLE_API_PAYLOAD = {
    "hourly": {
        "time": ["2099-01-01T00:00", "2099-01-01T01:00"],
        "temperature_2m": [10.0, 11.0],
        "apparent_temperature": [9.0, 10.0],
        "precipitation": [0.0, 0.5],
        "precipitation_probability": [10.0, 20.0],
        "windspeed_10m": [5.0, 6.0],
        "winddirection_10m": [180.0, 270.0],
        "relativehumidity_2m": [80.0, 75.0],
        "uv_index": [1.0, 2.0],
        "cloudcover": [30.0, 50.0],
    },
    "daily": {
        "time": ["2099-01-01", "2099-01-02"],
        "temperature_2m_max": [15.0, 16.0],
        "temperature_2m_min": [5.0, 6.0],
        "precipitation_sum": [0.5, 0.0],
        "precipitation_probability_max": [20.0, 5.0],
        "windspeed_10m_max": [10.0, 8.0],
        "winddirection_10m_dominant": [270.0, 180.0],
        "sunrise": ["2099-01-01T07:00", "2099-01-02T07:01"],
        "sunset": ["2099-01-01T17:00", "2099-01-02T16:59"],
    },
}


@pytest.fixture()
def tmp_db(monkeypatch, tmp_path):
    """Point the DB module at a fresh temp file and reset the ready flag."""
    db_file = tmp_path / "test_weather.db"
    monkeypatch.setenv("WEATHER_DB_PATH", str(db_file))
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    monkeypatch.setattr(db_module, "DATA_DIR", db_file.parent)
    monkeypatch.setattr(db_module, "_db_ready", False)
    yield db_file
    monkeypatch.setattr(db_module, "_db_ready", False)