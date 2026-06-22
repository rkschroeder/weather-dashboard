from pathlib import Path
import sqlite3
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "weather.db"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hourly (
            time TEXT PRIMARY KEY,
            temperature_2m REAL,
            precipitation REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily (
            date TEXT PRIMARY KEY,
            temp_max REAL,
            temp_min REAL,
            precipitation_sum REAL
        )
    """)
    conn.commit()
    return conn


def save_weather(data: dict) -> None:
    hourly_rows = list(zip(
        data["hourly"]["time"],
        data["hourly"]["temperature_2m"],
        data["hourly"]["precipitation"],
    ))
    daily_rows = list(zip(
        data["daily"]["time"],
        data["daily"]["temperature_2m_max"],
        data["daily"]["temperature_2m_min"],
        data["daily"]["precipitation_sum"],
    ))

    with _connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO hourly (time, temperature_2m, precipitation) VALUES (?, ?, ?)",
            hourly_rows,
        )
        conn.executemany(
            "INSERT OR REPLACE INTO daily (date, temp_max, temp_min, precipitation_sum) VALUES (?, ?, ?, ?)",
            daily_rows,
        )


def load_hourly() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["time", "temperature_2m", "precipitation"])
    with _connect() as conn:
        df = pd.read_sql("SELECT * FROM hourly ORDER BY time", conn, parse_dates=["time"])
    return df


def load_daily() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["date", "temp_max", "temp_min", "precipitation_sum"])
    with _connect() as conn:
        df = pd.read_sql("SELECT * FROM daily ORDER BY date", conn, parse_dates=["date"])
    return df