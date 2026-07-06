# Weather Dashboard

A 7-day weather forecast dashboard built with Streamlit, powered by the [Open-Meteo](https://open-meteo.com/) API. No API key required.

## Features

- Search by city name with persistent location history — previously fetched cities appear as one-click buttons in the sidebar
- Today's metrics as live cards: max/min temperature, apparent temperature (feels like), precipitation probability, precipitation, wind speed & direction (e.g. `→ W`), humidity, UV index, cloud cover, sunrise, and sunset
- Weekly summary table: date, conditions symbol, max/min temperature, precipitation, precipitation probability, wind speed, and peak UV — numbers are rounded to whole numbers for display
- **Threshold alerts** — configurable UV, precipitation, and max-temperature thresholds (sidebar form, whole numbers only, persisted to SQLite); days that exceed a threshold are highlighted in the table and listed in a warning banner
- 7-day forecast charts for temperature (with feels-like line), precipitation, wind speed, humidity, UV index, and cloud cover
- Data persisted in a local SQLite database

## Setup

Requires Python 3.10+ and [Poetry](https://python-poetry.org/).

```bash
cd weather_dashboard
poetry install
```

## Running the App

```bash
poetry run streamlit run weather_dashboard/app.py
```

Open `http://localhost:8501`.

### First Run

No forecast data has been fetched yet on a fresh install. The dashboard will display a welcome screen with three steps:

1. **Enter a city** — type any city name in the sidebar (default: *Berlin*).
2. **Search the city** — click **Search City**. If multiple locations match, select the correct one from the list.
3. **Fetch the forecast** — click **Fetch Weather** to load the 7-day forecast. Data is saved locally so subsequent loads are instant.

## Dashboard

After the first fetch, the dashboard shows three sections:

- **Metric cards** — three rows of four cards each:
  - *Row 1:* Max Temp, Min Temp, Apparent Temp (feels like), Precip Probability
  - *Row 2:* Precipitation, Wind Speed, Wind Direction, Humidity
  - *Row 3:* Peak UV Index, Avg Cloud Cover, Sunrise, Sunset
- **Weekly summary table** — a compact overview of the week: Date, Conditions, Max Temp, Min Temp, Precipitation, Precip Probability, Wind Speed, Peak UV. Cells exceeding a configured threshold are highlighted in amber. An info popover next to the table heading explains what each conditions symbol means.
- **Forecast charts** — 7-day charts for temperature (max, min, feels like), precipitation, wind speed, humidity, UV index, and cloud cover.

### Number Formatting

Numbers in the Weekly Summary table, the Alert Thresholds inputs, and the alert banner messages are **rounded to the nearest whole number** for display (e.g. a stored value of `9.2` shows as `9`). This is display-only — the values stored in SQLite and used for threshold comparisons keep full precision. Metric cards and charts elsewhere on the dashboard are unaffected and keep their usual decimal precision.

### Threshold Alerts

The sidebar's **Alert Thresholds** expander lets you set thresholds for peak UV index, daily precipitation (mm), and max temperature (°C) — defaults are UV > 7, precipitation > 10 mm, and max temp > 35°C (whole numbers only). Saved thresholds persist across restarts (stored in SQLite), and a Reset button restores the defaults. Any day whose value strictly exceeds its threshold:
- shows up in a grouped warning banner above the weekly summary table (e.g. "Wed 09: Peak UV Index 9 exceeds threshold of 7"), and
- has its cell highlighted amber in the table.

If no thresholds are exceeded, a success message is shown instead of the warning banner.

### Conditions Symbol

The **Conditions** symbol in the weekly summary table is derived from avg daily cloud cover (hourly data) and daily precipitation total. Precipitation takes priority over cloud cover.

| Symbol | Condition | Rule |
|--------|-----------|------|
| 🌧️ | Heavy rain | precipitation ≥ 5 mm |
| 🌦️ | Light rain | precipitation ≥ 0.5 mm |
| ☀️ | Sunny | cloud cover < 25% (or no cloud data) |
| ⛅ | Partly cloudy | cloud cover 25–59% |
| ☁️ | Cloudy | cloud cover ≥ 60% |

## Testing

The project includes a unit test suite (75 tests) covering all pipeline modules. No external services or live network calls are required — HTTP calls are mocked and each test gets an isolated SQLite database via a `tmp_db` fixture.

```bash
poetry run pytest tests/ -v
```

| Test module | What it covers |
|-------------|---------------|
| `test_utils.py` | `degrees_to_compass` — cardinal/intercardinal points, boundary rounding, wrap-around at 360° |
| `test_transform.py` | `parse_weather` — field order, empty arrays, missing key errors |
| `test_extract.py` | `geocode_city` / `fetch_weather` — success paths, fuzzy-match filtering, network errors, HTTP errors |
| `test_db.py` | `init_db` — table creation (all 4 tables), idempotency, migration guard for missing columns including `locations` |
| `test_load.py` | `upsert_weather` — inserts, upsert conflict replacement, metadata label writes, location row written/skipped; `save_alert_thresholds` — writes/overwrites the threshold config |
| `test_query.py` | `load_hourly` / `load_daily` / `load_location_label` / `load_location_history` — DataFrame shape, past-row filter, ordering, limit, empty-table default; `load_alert_thresholds` — defaults, partial merge, round-trip |
| `test_pipeline.py` | `run_pipeline` — ETL call order, default label, `FetchError` propagation |
| `test_alerts.py` | `merge_uv_into_daily` / `detect_alerts` — per-day UV merge, strict threshold comparison, message format, empty-input handling |

## Developer Tools

`run_pipeline.py` is a convenience script for running and verifying the ETL pipeline without opening the Streamlit app. Pass any city name as an argument:

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
├── tests/
│   ├── conftest.py            # Shared fixtures (tmp_db, SAMPLE_API_PAYLOAD)
│   ├── test_utils.py
│   ├── test_transform.py
│   ├── test_extract.py
│   ├── test_db.py
│   ├── test_load.py
│   ├── test_query.py
│   ├── test_pipeline.py
│   └── test_alerts.py
└── weather_dashboard/
    ├── pipeline/
    │   ├── __init__.py        # run_pipeline(lat, lon) — orchestrates ETL
    │   ├── extract.py         # Open-Meteo API + geocoding (Extract)
    │   ├── transform.py       # Parse raw JSON → row tuples (Transform)
    │   └── load.py            # Upsert rows into SQLite (Load)
    ├── db.py                  # DB connection + schema init
    ├── query.py               # Read DataFrames from SQLite
    ├── alerts.py              # Threshold-alert detection + table styling (no Streamlit/DB dependency)
    ├── utils.py               # Helper: degrees_to_compass
    └── app.py                 # Streamlit dashboard
```

## Database

Fetched data is saved to `data/weather.db` (SQLite, auto-created on first run) in two tables:

| Table | Columns |
|-------|---------|
| `hourly` | `time`, `temperature_2m`, `apparent_temperature`, `precipitation`, `precipitation_probability`, `wind_speed`, `wind_direction`, `humidity`, `uv_index`, `cloud_cover` |
| `daily` | `date`, `temp_max`, `temp_min`, `precipitation_sum`, `precipitation_probability_max`, `wind_speed_max`, `wind_direction_dominant`, `sunrise`, `sunset` |
| `locations` | `label`, `lat`, `lon`, `last_fetched` |
| `metadata` | `key`, `value` |

Re-fetching the same location upserts existing rows rather than duplicating them. Existing databases are migrated automatically to add any missing columns.

`metadata` stores the last-fetched city label (`last_location`) and the saved alert threshold config (`alert_thresholds`, JSON-encoded).