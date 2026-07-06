from datetime import datetime, timedelta, timezone

import pytest
from weather_dashboard.utils import degrees_to_compass, format_relative_time


@pytest.mark.parametrize("degrees, expected", [
    (0,     "↑"),   # N
    (90,    "→"),   # E
    (180,   "↓"),   # S
    (270,   "←"),   # W
    (45,    "↗"),   # NE
    (315,   "↖"),   # NW
    (135,   "↘"),   # SE
    (225,   "↙"),   # SW
    (360,   "↑"),   # wraps to N
    (359,   "↑"),   # rounds to N
    (22.5,  "↗"),   # boundary: rounds to index 1
    (337.5, "↑"),   # boundary: 337.5/22.5=15.0 → index 15 → N wrap-around entry
])
def test_degrees_to_compass(degrees, expected):
    assert degrees_to_compass(degrees) == expected


def _iso(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%d %H:%M:%S")


def test_format_relative_time_just_now():
    assert format_relative_time(_iso(timedelta(seconds=5))) == "just now"


def test_format_relative_time_minutes():
    assert format_relative_time(_iso(timedelta(minutes=5))) == "5m ago"


def test_format_relative_time_hours():
    assert format_relative_time(_iso(timedelta(hours=3))) == "3h ago"


def test_format_relative_time_days():
    assert format_relative_time(_iso(timedelta(days=2))) == "2d ago"


def test_format_relative_time_empty_string():
    assert format_relative_time("") == ""