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
    for sql in [
        "ALTER TABLE hourly ADD COLUMN wind_speed REAL",
        "ALTER TABLE hourly ADD COLUMN wind_direction REAL",
        "ALTER TABLE daily ADD COLUMN wind_speed_max REAL",
        "ALTER TABLE daily ADD COLUMN wind_direction_dominant REAL",
    ]:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn


def save_weather(data: dict) -> None:
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

    with _connect() as conn:
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
    with _connect() as conn:
        df = pd.read_sql("SELECT * FROM hourly ORDER BY time", conn, parse_dates=["time"])
    return df


def load_daily() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["date", "temp_max", "temp_min", "precipitation_sum", "wind_speed_max", "wind_direction_dominant"])
    with _connect() as conn:
        df = pd.read_sql("SELECT * FROM daily ORDER BY date", conn, parse_dates=["date"])
    return df