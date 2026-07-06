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


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
    # ALTER TABLE has no IF NOT EXISTS; PRAGMA check prevents duplicate-column errors
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def init_db() -> None:
    global _db_ready
    if _db_ready:  # run at most once per process
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
            # Migration guard: upgrade existing DBs that predate these columns
            _ensure_column(conn, "hourly", "humidity", "REAL")
            _ensure_column(conn, "hourly", "uv_index", "REAL")
            _ensure_column(conn, "hourly", "cloud_cover", "REAL")
            _ensure_column(conn, "hourly", "apparent_temperature", "REAL")
            _ensure_column(conn, "hourly", "precipitation_probability", "REAL")

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
            _ensure_column(conn, "daily", "sunrise", "TEXT")
            _ensure_column(conn, "daily", "sunset", "TEXT")
            _ensure_column(conn, "daily", "precipitation_probability_max", "REAL")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    label TEXT PRIMARY KEY,
                    lat   REAL NOT NULL,
                    lon   REAL NOT NULL,
                    last_fetched TEXT
                )
            """)
            _ensure_column(conn, "locations", "last_fetched", "TEXT")

    _db_ready = True