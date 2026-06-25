# CLAUDE.md

## Project Overview

7-day weather forecast dashboard. Fetches data from Open-Meteo (free, no API key), stores it in SQLite, and displays it via Streamlit.

## Run

```bash
# Streamlit dashboard
poetry run streamlit run weather_dashboard/app.py

# Pipeline from terminal (any city)
poetry run python run_pipeline.py Berlin
```

## Key Files

| File | Purpose |
|------|---------|
| `run_pipeline.py` | Developer convenience script — verify the pipeline from the terminal without opening the app |
| `weather_dashboard/pipeline/extract.py` | Open-Meteo forecast + geocoding API calls |
| `weather_dashboard/pipeline/transform.py` | Parse raw API JSON → typed row tuples |
| `weather_dashboard/pipeline/load.py` | Upsert rows into SQLite |
| `weather_dashboard/pipeline/__init__.py` | `run_pipeline(lat, lon)` — orchestrates Extract → Transform → Load |
| `weather_dashboard/db.py` | DB connection + schema init |
| `weather_dashboard/query.py` | `load_hourly()` / `load_daily()` — read DataFrames from DB |
| `weather_dashboard/app.py` | Streamlit UI — sidebar, metric cards, charts |
| `data/weather.db` | SQLite database with `hourly` and `daily` tables (auto-created) |

## Architecture Notes

- `geocode_city(city)` → converts a city name to geographic coordinates. Returns up to 15 `{lat, lon, label}` dicts via the Open-Meteo geocoding API. Called in two places: the app sidebar (Search City button, so the user can pick the right match when multiple locations share a name) and `run_pipeline.py` (CLI, before passing coordinates to the pipeline).
- `fetch_weather(lat, lon)` → returns raw JSON with `hourly` and `daily` keys; hourly fields include `temperature_2m`, `precipitation`, `windspeed_10m`, `winddirection_10m`, `relativehumidity_2m`, `cloudcover`; daily fields include `uv_index_max`, `sunrise`, `sunset`
- `parse_weather(data)` → transforms raw JSON into `(hourly_rows, daily_rows)` tuples
- `upsert_weather(hourly_rows, daily_rows)` → writes to SQLite with INSERT OR REPLACE
- `run_pipeline(lat, lon)` → single entry point for the full ETL; callable from Airflow or CLI
- Streamlit reruns the full script on every interaction; SQLite is the persistence layer
- `init_db()` runs a migration guard on startup: adds any missing columns to existing tables via `ALTER TABLE` so older databases are upgraded automatically

## UI — Daily Summary Table

The table shows: Date, Conditions symbol, Max Temp, Min Temp, Precipitation, Wind Speed.

The **Conditions** symbol is derived from avg daily cloud cover (hourly data) and daily precipitation total:

| Symbol | Condition | Rule |
|--------|-----------|------|
| 🌧️ | Heavy rain | precipitation ≥ 5 mm |
| 🌦️ | Light rain | precipitation ≥ 0.5 mm |
| ☀️ | Sunny | cloud cover < 25% (or no cloud data) |
| ⛅ | Partly cloudy | cloud cover 25–60% |
| ☁️ | Cloudy | cloud cover > 60% |

Precipitation takes priority over cloud cover (a rainy day can still be partly cloudy).

## Dependencies

Managed by Poetry. Core: `requests`, `pandas`, `streamlit`.