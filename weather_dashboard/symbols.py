import pandas as pd

# Pure logic, no Streamlit/DB imports — same reuse pattern as alerts.py / aggregate.py.
# Thresholds live here once; CONDITION_SYMBOLS' rule text is generated from them so the
# Weekly Summary table, its info popover legend, and weather_symbol() can't drift apart.

HEAVY_RAIN_MM = 5
LIGHT_RAIN_MM = 0.5
SUNNY_MAX_CLOUD = 25
PARTLY_CLOUDY_MAX_CLOUD = 60

CONDITION_SYMBOLS = [
    ("🌧️", "Heavy rain", f"Precipitation ≥ {HEAVY_RAIN_MM} mm"),
    ("🌦️", "Light rain", f"Precipitation ≥ {LIGHT_RAIN_MM} mm"),
    ("☀️", "Sunny", f"Cloud cover < {SUNNY_MAX_CLOUD}% (or no data)"),
    ("⛅", "Partly cloudy", f"Cloud cover {SUNNY_MAX_CLOUD}–{PARTLY_CLOUDY_MAX_CLOUD - 1}%"),
    ("☁️", "Cloudy", f"Cloud cover ≥ {PARTLY_CLOUDY_MAX_CLOUD}%"),
]


def weather_symbol(precipitation_sum, cloud_cover) -> str:
    # Precipitation takes priority over cloud cover — a rainy day can still have any
    # cloud cover reading, so precipitation must be evaluated first. Do not reorder.
    precip = precipitation_sum or 0
    if precip >= HEAVY_RAIN_MM:
        return CONDITION_SYMBOLS[0][0]
    if precip >= LIGHT_RAIN_MM:
        return CONDITION_SYMBOLS[1][0]
    if cloud_cover is None or pd.isna(cloud_cover):
        return CONDITION_SYMBOLS[2][0]
    if cloud_cover < SUNNY_MAX_CLOUD:
        return CONDITION_SYMBOLS[2][0]
    if cloud_cover < PARTLY_CLOUDY_MAX_CLOUD:
        return CONDITION_SYMBOLS[3][0]
    return CONDITION_SYMBOLS[4][0]
