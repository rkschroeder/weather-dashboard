import pandas as pd
import pytest

from weather_dashboard.alerts import merge_uv_into_daily, detect_alerts, DEFAULT_THRESHOLDS


@pytest.fixture
def daily_df():
    return pd.DataFrame({
        "date": pd.to_datetime(["2099-01-01", "2099-01-02"]),
        "temp_max": [20.0, 40.0],
        "precipitation_sum": [1.0, 12.0],
    })


@pytest.fixture
def hourly_df():
    return pd.DataFrame({
        "time": pd.to_datetime([
            "2099-01-01T00:00", "2099-01-01T12:00",
            "2099-01-02T00:00", "2099-01-02T12:00",
        ]),
        "uv_index": [2.0, 4.0, 6.0, 9.0],
    })


def test_merge_uv_into_daily_takes_daily_max(daily_df, hourly_df):
    merged = merge_uv_into_daily(daily_df, hourly_df)
    assert list(merged["uv_index"]) == [4.0, 9.0]


def test_merge_uv_into_daily_handles_missing_uv_column(daily_df):
    empty_hourly = pd.DataFrame({"time": pd.to_datetime([])})
    merged = merge_uv_into_daily(daily_df, empty_hourly)
    assert merged["uv_index"].isna().all()


def test_detect_alerts_flags_values_strictly_above_threshold(daily_df, hourly_df):
    merged = merge_uv_into_daily(daily_df, hourly_df)
    triggered = detect_alerts(merged, DEFAULT_THRESHOLDS)
    metrics = {a["metric"] for a in triggered}
    assert metrics == {"temp_max", "precipitation_sum", "uv_index"}
    # All three triggered alerts should be on day 2 (2099-01-02)
    assert all(a["date"] == pd.Timestamp("2099-01-02") for a in triggered)


def test_detect_alerts_value_exactly_at_threshold_does_not_trigger():
    daily = pd.DataFrame({
        "date": pd.to_datetime(["2099-01-01"]),
        "temp_max": [35.0],
        "precipitation_sum": [10.0],
        "uv_index": [7.0],
    })
    assert detect_alerts(daily, DEFAULT_THRESHOLDS) == []


def test_detect_alerts_message_format():
    daily = pd.DataFrame({
        "date": pd.to_datetime(["2099-01-01"]),
        "uv_index": [9.2],
    })
    triggered = detect_alerts(daily, {"uv_index": 7.0})
    assert len(triggered) == 1
    assert triggered[0]["message"] == "Thu 01: Peak UV Index 9.2 exceeds threshold of 7.0"


def test_detect_alerts_empty_dataframe_returns_empty_list():
    empty = pd.DataFrame({"date": pd.to_datetime([]), "temp_max": []})
    assert detect_alerts(empty, DEFAULT_THRESHOLDS) == []