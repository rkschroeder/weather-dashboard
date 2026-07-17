import pandas as pd

from weather_dashboard.aggregate import aggregate_hourly

# Pure pandas logic, no Streamlit/DB imports — safe to call from the UI, CLI, or a
# future Airflow task (same reuse pattern as pipeline.run_pipeline).

DEFAULT_THRESHOLDS = {
    "uv_index": 7.0,
    "precipitation_sum": 10.0,
    "temp_max": 35.0,
}

THRESHOLD_LABELS = {
    "uv_index": "Peak UV Index",
    "precipitation_sum": "Precipitation (mm)",
    "temp_max": "Max Temp (°C)",
}

# Maps the *display* column names used in app.py's daily summary table back to the
# underlying metric key, so style_exceeding can work off the rendered DataFrame.
DISPLAY_COLUMN_METRICS = {
    "Max (°C)": "temp_max",
    "Precip (mm)": "precipitation_sum",
    "Peak UV": "uv_index",
}


def merge_uv_into_daily(daily: pd.DataFrame, hourly: pd.DataFrame) -> pd.DataFrame:
    merged = daily.copy()
    uv_per_day = aggregate_hourly(hourly, "uv_index", "max")
    if uv_per_day.empty:
        merged["uv_index"] = None
    else:
        merged = merged.merge(uv_per_day, on="date", how="left")
    return merged


def detect_alerts(daily_with_uv: pd.DataFrame, thresholds: dict) -> list[dict]:
    alerts = []
    for _, row in daily_with_uv.iterrows():
        date = row["date"]
        for metric, threshold in thresholds.items():
            if metric not in daily_with_uv.columns:
                continue
            value = row[metric]
            # Strict > , matching "exceeds" — a value exactly at the threshold does not trigger.
            if pd.isna(value) or value <= threshold:
                continue
            label = THRESHOLD_LABELS.get(metric, metric)
            date_str = date.strftime("%a %d") if hasattr(date, "strftime") else str(date)
            alerts.append({
                "date": date,
                "metric": metric,
                "label": label,
                "value": value,
                "threshold": threshold,
                "message": f"{date_str}: {label} {value:.0f} exceeds threshold of {threshold:.0f}",
            })
    return alerts


def style_exceeding(row: pd.Series, thresholds: dict) -> list[str]:
    styles = []
    for col in row.index:
        metric = DISPLAY_COLUMN_METRICS.get(col)
        threshold = thresholds.get(metric) if metric else None
        value = row[col]
        if threshold is not None and pd.notna(value) and value > threshold:
            styles.append("background-color: rgba(251, 191, 36, 0.18)")
        else:
            styles.append("")
    return styles