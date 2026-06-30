import sqlite3
from contextlib import closing

from weather_dashboard.db import init_db
from weather_dashboard.pipeline.load import upsert_weather


HOURLY_ROWS = [
    ("2099-01-01T00:00", 10.0, 9.0, 0.0, 10.0, 5.0, 180.0, 80.0, 1.0, 30.0),
    ("2099-01-01T01:00", 11.0, 10.0, 0.5, 20.0, 6.0, 270.0, 75.0, 2.0, 50.0),
]

DAILY_ROWS = [
    ("2099-01-01", 15.0, 5.0, 0.5, 20.0, 10.0, 270.0, "2099-01-01T07:00", "2099-01-01T17:00"),
    ("2099-01-02", 16.0, 6.0, 0.0, 5.0,  8.0,  180.0, "2099-01-02T07:01", "2099-01-02T16:59"),
]


def _fetch_all(db_path, query):
    with closing(sqlite3.connect(db_path)) as conn:
        return conn.execute(query).fetchall()


def test_upsert_inserts_hourly_rows(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS)
    rows = _fetch_all(tmp_db, "SELECT time FROM hourly ORDER BY time")
    assert [r[0] for r in rows] == ["2099-01-01T00:00", "2099-01-01T01:00"]


def test_upsert_inserts_daily_rows(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS)
    rows = _fetch_all(tmp_db, "SELECT date FROM daily ORDER BY date")
    assert [r[0] for r in rows] == ["2099-01-01", "2099-01-02"]


def test_upsert_replaces_on_conflict(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS)
    # Re-insert with different temperature
    updated = [("2099-01-01T00:00", 99.0, 9.0, 0.0, 10.0, 5.0, 180.0, 80.0, 1.0, 30.0)]
    upsert_weather(updated, [])
    rows = _fetch_all(tmp_db, "SELECT temperature_2m FROM hourly WHERE time = '2099-01-01T00:00'")
    assert rows[0][0] == 99.0
    # Original row count unchanged
    all_rows = _fetch_all(tmp_db, "SELECT time FROM hourly")
    assert len(all_rows) == 2


def test_upsert_writes_label_to_metadata(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, label="Berlin, Germany")
    rows = _fetch_all(tmp_db, "SELECT value FROM metadata WHERE key = 'last_location'")
    assert rows[0][0] == "Berlin, Germany"


def test_upsert_empty_label_leaves_metadata_untouched(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, label="")
    rows = _fetch_all(tmp_db, "SELECT value FROM metadata WHERE key = 'last_location'")
    assert rows == []


def test_upsert_label_can_be_overwritten(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, label="Berlin")
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, label="Paris")
    rows = _fetch_all(tmp_db, "SELECT value FROM metadata WHERE key = 'last_location'")
    assert rows[0][0] == "Paris"