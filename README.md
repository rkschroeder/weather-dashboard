# Weather Dashboard

A simple 7-day weather forecast dashboard built with Streamlit, powered by the [Open-Meteo](https://open-meteo.com/) API. No API key required.

## Features

- Search by city name
- 7-day forecast for temperature (max/min) and precipitation
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

Open `http://localhost:8501`, type a city name in the sidebar, and click **Fetch & Refresh Data**.

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

Fetched data is saved to `data/weather.db` (SQLite, auto-created on first run) in two tables: `hourly` and `daily`. Re-fetching the same location upserts existing rows rather than duplicating them.