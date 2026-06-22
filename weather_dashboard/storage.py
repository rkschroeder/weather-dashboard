from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
HOURLY_CSV = DATA_DIR / "hourly.csv"
DAILY_CSV = DATA_DIR / "daily.csv"


def _ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def save_weather(data: dict) -> None:
    _ensure_data_dir()

    hourly = pd.DataFrame({
        "time": data["hourly"]["time"],
        "temperature_2m": data["hourly"]["temperature_2m"],
        "precipitation": data["hourly"]["precipitation"],
    })
    hourly["time"] = pd.to_datetime(hourly["time"])

    daily = pd.DataFrame({
        "date": data["daily"]["time"],
        "temp_max": data["daily"]["temperature_2m_max"],
        "temp_min": data["daily"]["temperature_2m_min"],
        "precipitation_sum": data["daily"]["precipitation_sum"],
    })
    daily["date"] = pd.to_datetime(daily["date"])

    _upsert(hourly, HOURLY_CSV, key="time")
    _upsert(daily, DAILY_CSV, key="date")


def _upsert(new_df: pd.DataFrame, path: Path, key: str) -> None:
    if path.exists():
        existing = pd.read_csv(path, parse_dates=[key])
        combined = pd.concat([existing, new_df]).drop_duplicates(subset=[key], keep="last")
    else:
        combined = new_df
    combined.sort_values(key).to_csv(path, index=False)


def load_hourly() -> pd.DataFrame:
    if not HOURLY_CSV.exists():
        return pd.DataFrame(columns=["time", "temperature_2m", "precipitation"])
    return pd.read_csv(HOURLY_CSV, parse_dates=["time"])


def load_daily() -> pd.DataFrame:
    if not DAILY_CSV.exists():
        return pd.DataFrame(columns=["date", "temp_max", "temp_min", "precipitation_sum"])
    return pd.read_csv(DAILY_CSV, parse_dates=["date"])