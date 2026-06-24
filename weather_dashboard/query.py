from contextlib import closing
import pandas as pd
from weather_dashboard.db import connect, DB_PATH


def load_hourly() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["time", "temperature_2m", "precipitation", "wind_speed", "wind_direction"])
    with closing(connect()) as conn:
        return pd.read_sql(
            "SELECT * FROM hourly WHERE time >= date('now', 'localtime') ORDER BY time",
            conn,
            parse_dates=["time"],
        )


def load_daily() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["date", "temp_max", "temp_min", "precipitation_sum", "wind_speed_max", "wind_direction_dominant"])
    with closing(connect()) as conn:
        return pd.read_sql(
            "SELECT * FROM daily WHERE date >= date('now', 'localtime') ORDER BY date",
            conn,
            parse_dates=["date"],
        )