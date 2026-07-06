from contextlib import closing
import pandas as pd
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
            "SELECT label, lat, lon FROM locations ORDER BY last_fetched DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"label": r[0], "lat": r[1], "lon": r[2]} for r in rows]