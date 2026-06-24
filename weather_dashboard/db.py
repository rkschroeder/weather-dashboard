import sqlite3
from contextlib import closing
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "weather.db"


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with closing(connect()) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly (
                    time TEXT PRIMARY KEY,
                    temperature_2m REAL,
                    precipitation REAL,
                    wind_speed REAL,
                    wind_direction REAL
                )
            """)
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