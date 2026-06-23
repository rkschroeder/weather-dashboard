from contextlib import closing
from pathlib import Path
import sqlite3
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "weather.db"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def _init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with closing(_connect()) as conn:
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


def save_weather(data: dict) -> None:
    try:
        hourly_rows = list(zip(
            data["hourly"]["time"],
            data["hourly"]["temperature_2m"],
            data["hourly"]["precipitation"],
            data["hourly"]["windspeed_10m"],
            data["hourly"]["winddirection_10m"],
        ))
        daily_rows = list(zip(
            data["daily"]["time"],
            data["daily"]["temperature_2m_max"],
            data["daily"]["temperature_2m_min"],
            data["daily"]["precipitation_sum"],
            data["daily"]["windspeed_10m_max"],
            data["daily"]["winddirection_10m_dominant"],
        ))
    except KeyError as e:
        raise ValueError(f"Unexpected weather data structure: missing field {e}") from e

    _init_db()
    with closing(_connect()) as conn:
        with conn:
            conn.executemany(
                "INSERT OR REPLACE INTO hourly (time, temperature_2m, precipitation, wind_speed, wind_direction) VALUES (?, ?, ?, ?, ?)",
                hourly_rows,
            )
            conn.executemany(
                "INSERT OR REPLACE INTO daily (date, temp_max, temp_min, precipitation_sum, wind_speed_max, wind_direction_dominant) VALUES (?, ?, ?, ?, ?, ?)",
                daily_rows,
            )


def load_hourly() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["time", "temperature_2m", "precipitation", "wind_speed", "wind_direction"])
    with closing(_connect()) as conn:
        return pd.read_sql(
            "SELECT * FROM hourly WHERE time >= date('now', 'localtime') ORDER BY time",
            conn,
            parse_dates=["time"],
        )


def load_daily() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["date", "temp_max", "temp_min", "precipitation_sum", "wind_speed_max", "wind_direction_dominant"])
    with closing(_connect()) as conn:
        return pd.read_sql(
            "SELECT * FROM daily WHERE date >= date('now', 'localtime') ORDER BY date",
            conn,
            parse_dates=["date"],
        )
