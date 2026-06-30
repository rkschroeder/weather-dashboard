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
                    apparent_temperature REAL,
                    precipitation REAL,
                    precipitation_probability REAL,
                    wind_speed REAL,
                    wind_direction REAL,
                    humidity REAL,
                    uv_index REAL,
                    cloud_cover REAL
                )
            """)
            existing = {col[1] for col in conn.execute("PRAGMA table_info(hourly)").fetchall()}
            if "humidity" not in existing:
                conn.execute("ALTER TABLE hourly ADD COLUMN humidity REAL")
            if "uv_index" not in existing:
                conn.execute("ALTER TABLE hourly ADD COLUMN uv_index REAL")
            if "cloud_cover" not in existing:
                conn.execute("ALTER TABLE hourly ADD COLUMN cloud_cover REAL")
            if "apparent_temperature" not in existing:
                conn.execute("ALTER TABLE hourly ADD COLUMN apparent_temperature REAL")
            if "precipitation_probability" not in existing:
                conn.execute("ALTER TABLE hourly ADD COLUMN precipitation_probability REAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily (
                    date TEXT PRIMARY KEY,
                    temp_max REAL,
                    temp_min REAL,
                    precipitation_sum REAL,
                    precipitation_probability_max REAL,
                    wind_speed_max REAL,
                    wind_direction_dominant REAL,
                    sunrise TEXT,
                    sunset TEXT
                )
            """)
            daily_existing = {col[1] for col in conn.execute("PRAGMA table_info(daily)").fetchall()}
            if "sunrise" not in daily_existing:
                conn.execute("ALTER TABLE daily ADD COLUMN sunrise TEXT")
            if "sunset" not in daily_existing:
                conn.execute("ALTER TABLE daily ADD COLUMN sunset TEXT")
            if "precipitation_probability_max" not in daily_existing:
                conn.execute("ALTER TABLE daily ADD COLUMN precipitation_probability_max REAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
    _db_ready = True