# Weather Dashboard

A 7-day weather forecast dashboard built with Streamlit, powered by the [Open-Meteo](https://open-meteo.com/) API. No API key required.

## Features

- Search by city name
- 7-day forecast for temperature (max/min), precipitation, and wind speed
- Wind direction displayed as arrow + compass label (e.g. `→ W`)
- Data persisted in a local SQLite database

## Setup

Requires Python 3.10+ and [Poetry](https://python-poetry.org/).

```bash
cd weather_dashboard
poetry install
```

## Run

```bash
poetry run streamlit run weather_dashboard/app.py
```

Open `http://localhost:8501`.

## First Run

When you open the app for the first time, no forecast data has been fetched yet. The dashboard will display a welcome screen with three steps to guide you:

1. **Enter a city** — type any city name in the sidebar (default: *Berlin*).
2. **Search the city** — click **Search City**. If multiple locations match, select the correct one from the list.
3. **Fetch the forecast** — click **Fetch Weather** to load the 7-day forecast. Data is saved locally so subsequent loads are instant.

After the first fetch the full dashboard appears: today's metrics (temperature, precipitation, wind), 7-day charts, and a daily summary table.

## Project Structure

```
weather_dashboard/
├── data/                  # SQLite database (weather.db)
└── weather_dashboard/
    ├── fetch.py           # Open-Meteo API + geocoding
    ├── storage.py         # SQLite read/write with upsert
    └── app.py             # Streamlit dashboard
```

## Data

Fetched data is saved to `data/weather.db` (SQLite, auto-created on first run) in two tables:

| Table | Columns |
|-------|---------|
| `hourly` | `time`, `temperature_2m`, `precipitation`, `wind_speed`, `wind_direction` |
| `daily` | `date`, `temp_max`, `temp_min`, `precipitation_sum`, `wind_speed_max`, `wind_direction_dominant` |

Re-fetching the same location upserts existing rows rather than duplicating them. Existing databases are migrated automatically to include the wind columns.