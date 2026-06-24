# CLAUDE.md

## Project Overview

7-day weather forecast dashboard. Fetches data from Open-Meteo (free, no API key), stores it in SQLite, and displays it via Streamlit.

## Run

```bash
# Streamlit dashboard
poetry run streamlit run weather_dashboard/app.py

# Pipeline from terminal (any city)
poetry run python run_pipeline.py
 Berlin
```

## Key Files

| File | Purpose |
|------|---------|
| `run_pipeline.py` | CLI script — geocode city, run ETL, print forecast |
| `weather_dashboard/pipeline/extract.py` | Open-Meteo forecast + geocoding API calls |
| `weather_dashboard/pipeline/transform.py` | Parse raw API JSON → typed row tuples |
| `weather_dashboard/pipeline/load.py` | Upsert rows into SQLite |
| `weather_dashboard/pipeline/__init__.py` | `run_pipeline(lat, lon)` — orchestrates Extract → Transform → Load |
| `weather_dashboard/db.py` | DB connection + schema init |
| `weather_dashboard/query.py` | `load_hourly()` / `load_daily()` — read DataFrames from DB |
| `weather_dashboard/app.py` | Streamlit UI — sidebar, metric cards, charts |
| `data/weather.db` | SQLite database with `hourly` and `daily` tables (auto-created) |

## Architecture Notes

- `geocode_city(city)` → returns list of `{lat, lon, label}` dicts using Open-Meteo geocoding API
- `fetch_weather(lat, lon)` → returns raw JSON with `hourly` and `daily` keys
- `parse_weather(data)` → transforms raw JSON into `(hourly_rows, daily_rows)` tuples
- `upsert_weather(hourly_rows, daily_rows)` → writes to SQLite with INSERT OR REPLACE
- `run_pipeline(lat, lon)` → single entry point for the full ETL; callable from Airflow or CLI
- Streamlit reruns the full script on every interaction; SQLite is the persistence layer

## Dependencies

Managed by Poetry. Core: `requests`, `pandas`, `streamlit`.