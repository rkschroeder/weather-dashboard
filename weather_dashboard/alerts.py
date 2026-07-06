import pandas as pd

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
    if "uv_index" in hourly.columns and not hourly.empty:
        uv_per_day = (
            hourly.assign(date=hourly["time"].dt.normalize())
            .groupby("date", as_index=False)["uv_index"]
            .max()
        )
        merged = merged.merge(uv_per_day, on="date", how="left")
    else:
        merged["uv_index"] = None
    return merged


def detect_alerts(daily_with_uv: pd.DataFrame, thresholds: dict) -> list[dict]:
    alerts = []
    for _, row in daily_with_uv.iterrows():
        date = row["date"]
        for metric, threshold in thresholds.items():
            if metric not in daily_with_uv.columns:
                continue
            value = row[metric]
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
                "message": f"{date_str}: {label} {value:.1f} exceeds threshold of {threshold:.1f}",
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