import pytest
from weather_dashboard.utils import degrees_to_compass


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