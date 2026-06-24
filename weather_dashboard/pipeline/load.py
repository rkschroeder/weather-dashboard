from contextlib import closing
from weather_dashboard.db import connect, init_db


def upsert_weather(hourly_rows: list[tuple], daily_rows: list[tuple]) -> None:
    init_db()
    with closing(connect()) as conn:
        with conn:
            conn.executemany(
                "INSERT OR REPLACE INTO hourly (time, temperature_2m, precipitation, wind_speed, wind_direction) VALUES (?, ?, ?, ?, ?)",
                hourly_rows,
            )
            conn.executemany(
                "INSERT OR REPLACE INTO daily (date, temp_max, temp_min, precipitation_sum, wind_speed_max, wind_direction_dominant) VALUES (?, ?, ?, ?, ?, ?)",
                daily_rows,
            )