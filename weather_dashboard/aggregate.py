import pandas as pd

# Pure pandas logic, no Streamlit/DB imports — safe to call from the UI, CLI, or a
# future Airflow task (same reuse pattern as alerts.py / pipeline.run_pipeline).


def aggregate_hourly(hourly: pd.DataFrame, column: str, how: str) -> pd.DataFrame:
    """One row per day for `column`, aggregated with `how` (e.g. 'mean', 'max').

    Returns an empty but correctly shaped DataFrame (columns ['date', column])
    if `hourly` is empty or lacks `column` — callers should branch on
    `.empty`, not re-check column existence themselves.
    """
    if hourly.empty or column not in hourly.columns:
        return pd.DataFrame(columns=["date", column])
    return (
        hourly.assign(date=hourly["time"].dt.normalize())
        .groupby("date", as_index=False)[column]
        .agg(how)
    )
