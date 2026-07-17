import pandas as pd

from weather_dashboard.aggregate import aggregate_hourly


def _hourly_df():
    return pd.DataFrame({
        "time": pd.to_datetime([
            "2099-01-01T00:00", "2099-01-01T12:00",
            "2099-01-02T00:00", "2099-01-02T12:00",
        ]),
        "cloud_cover": [10.0, 30.0, 60.0, 80.0],
    })


def test_aggregate_hourly_mean_per_day():
    result = aggregate_hourly(_hourly_df(), "cloud_cover", "mean")
    assert list(result["date"]) == [pd.Timestamp("2099-01-01"), pd.Timestamp("2099-01-02")]
    assert list(result["cloud_cover"]) == [20.0, 70.0]


def test_aggregate_hourly_max_per_day():
    result = aggregate_hourly(_hourly_df(), "cloud_cover", "max")
    assert list(result["cloud_cover"]) == [30.0, 80.0]


def test_aggregate_hourly_empty_hourly_returns_empty_shaped_frame():
    empty = pd.DataFrame({"time": pd.to_datetime([]), "cloud_cover": []})
    result = aggregate_hourly(empty, "cloud_cover", "mean")
    assert result.empty
    assert list(result.columns) == ["date", "cloud_cover"]


def test_aggregate_hourly_missing_column_returns_empty_shaped_frame():
    hourly = pd.DataFrame({"time": pd.to_datetime(["2099-01-01T00:00"])})
    result = aggregate_hourly(hourly, "uv_index", "max")
    assert result.empty
    assert list(result.columns) == ["date", "uv_index"]