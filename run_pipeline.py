import logging
import sys
logging.basicConfig(level=logging.INFO, format="%(message)s")

from weather_dashboard.pipeline.extract import geocode_city
from weather_dashboard.pipeline import run_pipeline
from weather_dashboard.query import load_daily

city = sys.argv[1] if len(sys.argv) > 1 else "Berlin"

locations = geocode_city(city)
loc = locations[0]
print(f"Location: {loc['label']} ({loc['lat']}, {loc['lon']})")

run_pipeline(loc["lat"], loc["lon"])

print("\n--- Daily forecast ---")
print(load_daily()[["date", "temp_max", "temp_min", "precipitation_sum", "wind_speed_max", "wind_direction_dominant"]].to_string(index=False))