# Weather Dashboard

A 7-day weather forecast dashboard built with Streamlit, powered by the [Open-Meteo](https://open-meteo.com/) API. No API key required.

## Features

- Search by city name
- 7-day forecast for temperature (max/min), precipitation, wind speed, humidity, UV index, cloud cover, sunrise, and sunset
- Today's metrics displayed as live cards: temperature, precipitation, wind, humidity, UV index, cloud cover, sunrise, and sunset
- Wind direction displayed as arrow compass label (e.g. `→ W`)
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

After the first fetch the full dashboard appears: today's metric cards (max/min temperature, precipitation, wind speed, wind direction, humidity, UV index, cloud cover, sunrise, and sunset), 7-day forecast charts (temperature, precipitation, wind speed, humidity, UV index, cloud cover), and a daily summary table.

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
| `hourly` | `time`, `temperature_2m`, `precipitation`, `wind_speed`, `wind_direction`, `humidity`, `uv_index`, `cloud_cover` |
| `daily` | `date`, `temp_max`, `temp_min`, `precipitation_sum`, `wind_speed_max`, `wind_direction_dominant`, `sunrise`, `sunset` |

Re-fetching the same location upserts existing rows rather than duplicating them. Existing databases are migrated automatically to add any missing columns.