import logging
import sys
logging.basicConfig(level=logging.INFO, format="%(message)s")

from weather_dashboard.pipeline.extract import geocode_city
from weather_dashboard.pipeline import run_pipeline
from weather_dashboard.query import load_daily, load_hourly

city = sys.argv[1] if len(sys.argv) > 1 else "Berlin"

locations = geocode_city(city)
loc = locations[0]

if len(locations) > 1:
    print(f"Warning: {len(locations)} matches found for '{city}'. Using the first result.")
    print("Other matches:")
    for alt in locations[1:]:
        print(f"  - {alt['label']} ({alt['lat']}, {alt['lon']})")
    print()

print(f"Location: {loc['label']} ({loc['lat']}, {loc['lon']})")

run_pipeline(loc["lat"], loc["lon"], label=loc["label"])

print("\n--- Daily forecast ---")
daily = load_daily()
hourly = load_hourly()

if "humidity" in hourly.columns:
    humidity_daily = (
        hourly.assign(date=hourly["time"].dt.normalize())
        .groupby("date", as_index=False)["humidity"]
        .mean()
        .rename(columns={"humidity": "avg_humidity"})
    )
    daily = daily.merge(humidity_daily, on="date", how="left")
    daily["avg_humidity"] = daily["avg_humidity"].round(0).astype("Int64")

if "uv_index" in hourly.columns:
    uv_daily = (
        hourly.assign(date=hourly["time"].dt.normalize())
        .groupby("date", as_index=False)["uv_index"]
        .max()
        .rename(columns={"uv_index": "peak_uv"})
    )
    daily = daily.merge(uv_daily, on="date", how="left")
    daily["peak_uv"] = daily["peak_uv"].round(1)

if "sunrise" in daily.columns:
    daily["sunrise"] = daily["sunrise"].str[11:16]
if "sunset" in daily.columns:
    daily["sunset"] = daily["sunset"].str[11:16]

cols = ["date", "temp_max", "temp_min", "precipitation_sum", "wind_speed_max", "wind_direction_dominant"]
if "avg_humidity" in daily.columns:
    cols.append("avg_humidity")
if "peak_uv" in daily.columns:
    cols.append("peak_uv")
if "sunrise" in daily.columns:
    cols.append("sunrise")
if "sunset" in daily.columns:
    cols.append("sunset")
print(daily[cols].to_string(index=False))