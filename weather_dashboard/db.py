import os
import sqlite3
from contextlib import closing
from pathlib import Path

_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "weather.db"
DB_PATH = Path(os.environ.get("WEATHER_DB_PATH", _DEFAULT_DB_PATH))
DATA_DIR = DB_PATH.parent

_db_ready = False


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    global _db_ready
    if _db_ready:
        return
    DATA_DIR.mkdir(exist_ok=True)
    with closing(connect()) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly (
                    time TEXT PRIMARY KEY,
                    temperature_2m REAL,
                    precipitation REAL,
                    wind_speed REAL,
                    wind_direction REAL,
                    humidity REAL
                )
            """)
            existing = {col[1] for col in conn.execute("PRAGMA table_info(hourly)").fetchall()}
            if "humidity" not in existing:
                conn.execute("ALTER TABLE hourly ADD COLUMN humidity REAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily (
                    date TEXT PRIMARY KEY,
                    temp_max REAL,
                    temp_min REAL,
                    precipitation_sum REAL,
                    wind_speed_max REAL,
                    wind_direction_dominant REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
    _db_ready = True