import sqlite3
from contextlib import closing

from weather_dashboard.db import init_db
from weather_dashboard.pipeline.load import upsert_weather, save_alert_thresholds


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


def test_upsert_inserts_location_row(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, lat=52.5, lon=13.4, label="Berlin, Germany")
    rows = _fetch_all(tmp_db, "SELECT label, lat, lon FROM locations")
    assert rows == [("Berlin, Germany", 52.5, 13.4)]


def test_upsert_location_replaces_on_conflict(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, lat=52.5, lon=13.4, label="Berlin, Germany")
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, lat=52.5, lon=13.4, label="Berlin, Germany")
    rows = _fetch_all(tmp_db, "SELECT label FROM locations")
    assert len(rows) == 1


def test_upsert_no_location_row_without_label(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, lat=52.5, lon=13.4, label="")
    rows = _fetch_all(tmp_db, "SELECT label FROM locations")
    assert rows == []


def test_upsert_no_location_row_without_coords(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, label="Berlin, Germany")
    rows = _fetch_all(tmp_db, "SELECT label FROM locations")
    assert rows == []


def test_upsert_writes_utc_offset_to_metadata(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, utc_offset_seconds=3600)
    rows = _fetch_all(tmp_db, "SELECT value FROM metadata WHERE key = 'location_utc_offset'")
    assert int(rows[0][0]) == 3600


def test_upsert_utc_offset_can_be_overwritten(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, utc_offset_seconds=3600)
    upsert_weather(HOURLY_ROWS, DAILY_ROWS, utc_offset_seconds=-18000)
    rows = _fetch_all(tmp_db, "SELECT value FROM metadata WHERE key = 'location_utc_offset'")
    assert int(rows[0][0]) == -18000


def test_upsert_omitted_utc_offset_leaves_metadata_untouched(tmp_db):
    init_db()
    upsert_weather(HOURLY_ROWS, DAILY_ROWS)
    rows = _fetch_all(tmp_db, "SELECT value FROM metadata WHERE key = 'location_utc_offset'")
    assert rows == []


def test_save_alert_thresholds_writes_metadata(tmp_db):
    init_db()
    save_alert_thresholds({"uv_index": 5.0, "precipitation_sum": 15.0, "temp_max": 30.0})
    rows = _fetch_all(tmp_db, "SELECT value FROM metadata WHERE key = 'alert_thresholds'")
    assert rows[0][0] == '{"uv_index": 5.0, "precipitation_sum": 15.0, "temp_max": 30.0}'


def test_save_alert_thresholds_overwrites_existing(tmp_db):
    init_db()
    save_alert_thresholds({"uv_index": 5.0, "precipitation_sum": 15.0, "temp_max": 30.0})
    save_alert_thresholds({"uv_index": 8.0, "precipitation_sum": 12.0, "temp_max": 40.0})
    rows = _fetch_all(tmp_db, "SELECT value FROM metadata WHERE key = 'alert_thresholds'")
    assert len(rows) == 1
    assert rows[0][0] == '{"uv_index": 8.0, "precipitation_sum": 12.0, "temp_max": 40.0}'