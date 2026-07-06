import logging
from weather_dashboard.db import init_db
from weather_dashboard.pipeline.extract import fetch_weather, FetchError
from weather_dashboard.pipeline.transform import parse_weather
from weather_dashboard.pipeline.load import upsert_weather, save_alert_thresholds

logger = logging.getLogger(__name__)

__all__ = ["run_pipeline", "FetchError", "save_alert_thresholds"]


def run_pipeline(latitude: float, longitude: float, label: str = "") -> None:
    """Extract → Transform → Load for one location. Safe to call from Airflow or CLI."""
    logger.info("Pipeline start: lat=%s, lon=%s", latitude, longitude)

    init_db()
    raw = fetch_weather(latitude, longitude)
    hourly_rows, daily_rows = parse_weather(raw)
    upsert_weather(hourly_rows, daily_rows, lat=latitude, lon=longitude, label=label)

    logger.info("Pipeline complete: %d hourly, %d daily rows upserted", len(hourly_rows), len(daily_rows))
