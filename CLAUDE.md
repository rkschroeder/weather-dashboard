# CLAUDE.md

## Project Overview

7-day weather forecast dashboard. Fetches data from Open-Meteo (free, no API key), stores it as CSV, and displays it via Streamlit.

## Run

```bash
poetry run streamlit run weather_dashboard/app.py
```

## Key Files

| File | Purpose |
|------|---------|
| `weather_dashboard/fetch.py` | Open-Meteo forecast + geocoding API calls |
| `weather_dashboard/storage.py` | Save/load CSV; upserts to avoid duplicates |
| `weather_dashboard/app.py` | Streamlit UI — sidebar, metric cards, charts |
| `data/hourly.csv` | Hourly temperature & precipitation (auto-created) |
| `data/daily.csv` | Daily max/min temp & precipitation (auto-created) |

## Architecture Notes

- `geocode_city(city)` → returns `(lat, lon, label)` using Open-Meteo geocoding API
- `fetch_weather(lat, lon)` → returns raw JSON with `hourly` and `daily` keys
- `save_weather(data)` → parses JSON and upserts both CSVs
- Streamlit reruns the full script on every interaction; CSV is the persistence layer

## Dependencies

Managed by Poetry. Core: `requests`, `pandas`, `streamlit`.