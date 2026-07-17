import pandas as pd

from weather_dashboard.symbols import weather_symbol


def test_weather_symbol_heavy_rain():
    assert weather_symbol(5.0, 90) == "🌧️"


def test_weather_symbol_light_rain():
    assert weather_symbol(0.5, 90) == "🌦️"


def test_weather_symbol_precipitation_takes_priority_over_cloud_cover():
    # A rainy day can still have any cloud cover reading — precipitation wins.
    assert weather_symbol(5.0, 0) == "🌧️"


def test_weather_symbol_sunny():
    assert weather_symbol(0.0, 10) == "☀️"


def test_weather_symbol_sunny_when_cloud_cover_missing():
    assert weather_symbol(0.0, None) == "☀️"
    assert weather_symbol(0.0, float("nan")) == "☀️"
    assert weather_symbol(0.0, pd.NA) == "☀️"


def test_weather_symbol_partly_cloudy():
    assert weather_symbol(0.0, 25) == "⛅"
    assert weather_symbol(0.0, 59) == "⛅"


def test_weather_symbol_cloudy():
    assert weather_symbol(0.0, 60) == "☁️"
    assert weather_symbol(0.0, 100) == "☁️"


def test_weather_symbol_precipitation_none_treated_as_zero():
    assert weather_symbol(None, 10) == "☀️"