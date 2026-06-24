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

## Run the pipeline from the terminal

`run_pipeline.py` is a developer convenience script for running and verifying the pipeline without opening the Streamlit app. Pass any city name as an argument:

```bash
poetry run python run_pipeline.py Berlin
poetry run python run_pipeline.py "New York"
```

It geocodes the city, runs the full ETL pipeline, and prints the resulting 7-day forecast to the terminal.

## Project Structure

```
weather_dashboard/
├── run_pipeline.py            # CLI script — run the pipeline from the terminal
├── data/                      # SQLite database (weather.db, auto-created)
└── weather_dashboard/
    ├── pipeline/
    │   ├── __init__.py        # run_pipeline(lat, lon) — orchestrates ETL
    │   ├── extract.py         # Open-Meteo API + geocoding (Extract)
    │   ├── transform.py       # Parse raw JSON → row tuples (Transform)
    │   └── load.py            # Upsert rows into SQLite (Load)
    ├── db.py                  # DB connection + schema init
    ├── query.py               # Read DataFrames from SQLite
    ├── utils.py               # Helper: degrees_to_compass
    └── app.py                 # Streamlit dashboard
```

## Data

Fetched data is saved to `data/weather.db` (SQLite, auto-created on first run) in two tables:

| Table | Columns |
|-------|---------|
| `hourly` | `time`, `temperature_2m`, `precipitation`, `wind_speed`, `wind_direction` |
| `daily` | `date`, `temp_max`, `temp_min`, `precipitation_sum`, `wind_speed_max`, `wind_direction_dominant` |

Re-fetching the same location upserts existing rows rather than duplicating them. Existing databases are migrated automatically to include the wind columns.