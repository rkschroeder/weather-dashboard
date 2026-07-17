import json
from contextlib import closing
from weather_dashboard.db import connect


def upsert_weather(
    hourly_rows: list[tuple],
    daily_rows: list[tuple],
    lat: float | None = None,
    lon: float | None = None,
    label: str = "",
    utc_offset_seconds: int | None = None,
) -> None:
    with closing(connect()) as conn:
        with conn:
            conn.executemany(
                "INSERT OR REPLACE INTO hourly (time, temperature_2m, apparent_temperature, precipitation, precipitation_probability, wind_speed, wind_direction, humidity, uv_index, cloud_cover) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                hourly_rows,
            )
            conn.executemany(
                "INSERT OR REPLACE INTO daily (date, temp_max, temp_min, precipitation_sum, precipitation_probability_max, wind_speed_max, wind_direction_dominant, sunrise, sunset) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                daily_rows,
            )
            if label:
                conn.execute(
                    "INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_location', ?)",
                    (label,),
                )
            if utc_offset_seconds is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO metadata (key, value) VALUES ('location_utc_offset', ?)",
                    (utc_offset_seconds,),
                )
            if label and lat is not None and lon is not None:
                conn.execute(
                    "INSERT OR REPLACE INTO locations (label, lat, lon, last_fetched) VALUES (?, ?, ?, datetime('now'))",
                    (label, lat, lon),
                )


def save_alert_thresholds(thresholds: dict) -> None:
    with closing(connect()) as conn:
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES ('alert_thresholds', ?)",
                (json.dumps(thresholds),),
            )