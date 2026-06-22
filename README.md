# Weather Dashboard

A simple 7-day weather forecast dashboard built with Streamlit, powered by the [Open-Meteo](https://open-meteo.com/) API. No API key required.

## Features

- Search by city name
- 7-day forecast for temperature (max/min) and precipitation
- Data stored locally as CSV files

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
├── data/                  # CSV files (hourly.csv, daily.csv)
└── weather_dashboard/
    ├── fetch.py           # Open-Meteo API + geocoding
    ├── storage.py         # CSV read/write with deduplication
    └── app.py             # Streamlit dashboard
```

## Data

Fetched data is saved to `data/hourly.csv` and `data/daily.csv`. Re-fetching the same location updates existing rows rather than duplicating them.