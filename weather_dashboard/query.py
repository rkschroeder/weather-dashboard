import json
from contextlib import closing
import pandas as pd
from weather_dashboard.alerts import DEFAULT_THRESHOLDS
from weather_dashboard.db import connect, init_db


def load_hourly() -> pd.DataFrame:
    init_db()
    with closing(connect()) as conn:
        return pd.read_sql(
            "SELECT * FROM hourly WHERE time >= date('now', 'localtime') ORDER BY time",
            conn,
            parse_dates=["time"],
        )


def load_daily() -> pd.DataFrame:
    init_db()
    with closing(connect()) as conn:
        return pd.read_sql(
            "SELECT * FROM daily WHERE date >= date('now', 'localtime') ORDER BY date",
            conn,
            parse_dates=["date"],
        )


def load_location_label() -> str:
    init_db()
    with closing(connect()) as conn:
        row = conn.execute("SELECT value FROM metadata WHERE key = 'last_location'").fetchone()
        return row[0] if row else ""


def load_location_history(limit: int = 10) -> list[dict]:
    init_db()
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT label, lat, lon, last_fetched FROM locations ORDER BY last_fetched DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"label": r[0], "lat": r[1], "lon": r[2], "last_fetched": r[3]} for r in rows]


def load_alert_thresholds() -> dict:
    init_db()
    with closing(connect()) as conn:
        row = conn.execute("SELECT value FROM metadata WHERE key = 'alert_thresholds'").fetchone()
    if not row:
        return DEFAULT_THRESHOLDS.copy()
    return {**DEFAULT_THRESHOLDS, **json.loads(row[0])}