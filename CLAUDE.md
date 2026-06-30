# CLAUDE.md

## Project Overview

7-day weather forecast dashboard. Fetches data from the Open-Meteo API (free, no API key), stores it in SQLite, and displays it via Streamlit. The ETL pipeline is the single source of data — the UI only reads from SQLite.

**Tech stack:** Python 3.10+, Poetry, Pandas. Streamlit, SQLite.

---

## Current Status

### Implemented features

**ETL pipeline**
- Geocodes any city name via Open-Meteo geocoding API (up to 15 results, fuzzy-match filtered)
- Fetches 7-day hourly + daily forecast from Open-Meteo forecast API
- Upserts data into SQLite (`INSERT OR REPLACE` — idempotent, no duplicates)
- Auto-migration guard: existing databases are upgraded when new columns are added

**Hourly fields stored:** `temperature_2m`, `apparent_temperature`, `precipitation`, `precipitation_probability`, `wind_speed`, `wind_direction`, `humidity`, `uv_index`, `cloud_cover`

**Daily fields stored:** `temp_max`, `temp_min`, `precipitation_sum`, `precipitation_probability_max`, `wind_speed_max`, `wind_direction_dominant`, `sunrise`, `sunset`

**Dashboard UI**
- Sidebar: city search, geocode results picker, Fetch Weather button
- Metric cards — 3 rows of 4:
  - Temperatures: Max Temp, Min Temp, Apparent Temp, Precip Probability
  - Conditions: Precipitation, Wind Speed, Wind Direction, Humidity
  - Other: Peak UV Index, Cloud Cover, Sunrise, Sunset
- Daily summary table: Date, Conditions symbol, Max Temp, Min Temp, Precipitation, Precip Probability, Wind Speed
- Forecast charts (Altair, 2-column layout):
  - Temperature: shaded band + Max/Min/Feels Like lines with color legend and point markers
  - Precipitation: intensity-gradient bars (blue scale by mm)
  - Wind Speed | Humidity
  - Peak UV Index | Cloud Cover

---

## Next Steps

Potential improvements roughly in priority order:

1. **Hourly forecast view** — current charts aggregate hourly data to daily; add a toggle or separate section showing true hourly detail (e.g. hourly temperature curve for today)
2. **Location history** — remember previously fetched cities in `st.session_state` or a `locations` metadata table so users can switch without re-searching
3. **Threshold alerts** — highlight days in the daily table that exceed user-defined thresholds (e.g. UV > 7, precipitation > 10 mm, temperature > 35°C)
4. **Wind chill / heat index** — derive and display alongside apparent temperature for more context
5. **Snowfall field** — add `snowfall` and `snowfall_sum` from Open-Meteo (same extension pattern as existing fields)
6. **CSV export** — add a download button (`st.download_button`) for the daily summary DataFrame
7. **Multi-city comparison** — allow fetching multiple cities and overlaying them on the same chart
8. **Deploy to Streamlit Cloud** — add `requirements.txt` export (`poetry export`) and `secrets.toml` stub, document deployment steps
9. **Automated refresh** — schedule the pipeline via Airflow or a simple cron job so data stays fresh without manual Fetch clicks

---

## Commands

```bash
# Run the Streamlit dashboard
poetry run streamlit run weather_dashboard/app.py

# Run the ETL pipeline from the terminal (any city)
poetry run python run_pipeline.py Berlin
poetry run python run_pipeline.py "New York"

# Run the unit test suite
poetry run pytest tests/ -v
```

---

## Testing

The project uses **pytest** (dev dependency). Run with:

```bash
poetry run pytest tests/ -v
```

50 unit tests, all passing. No external services or live network calls — HTTP is mocked via `unittest.mock.patch` and each DB-touching test uses an isolated SQLite file via the `tmp_db` fixture in `conftest.py`.

### Test modules

| File | Covers |
|------|--------|
| `tests/conftest.py` | `tmp_db` fixture (redirects `DB_PATH` to a temp file, resets `_db_ready` between tests); `SAMPLE_API_PAYLOAD` shared fixture |
| `tests/test_utils.py` | `degrees_to_compass` — all cardinal/intercardinal directions, boundary rounding, 360° wrap-around |
| `tests/test_transform.py` | `parse_weather` — correct field order, empty arrays, missing key raises `ValueError` |
| `tests/test_extract.py` | `geocode_city` / `fetch_weather` — success, fuzzy-match filter, no-results, network errors, HTTP errors |
| `tests/test_db.py` | `init_db` — creates all 3 tables, idempotency, migration guard adds missing columns to existing DB |
| `tests/test_load.py` | `upsert_weather` — inserts rows, upsert replaces on PK conflict, label written/overwritten/skipped |
| `tests/test_query.py` | `load_hourly` / `load_daily` / `load_location_label` — DataFrame columns, past-row filter, empty-table default |
| `tests/test_pipeline.py` | `run_pipeline` — ETL call order and arguments, default label, `FetchError` propagation |

### `tmp_db` fixture

Defined in `conftest.py`. For each test it:
1. Creates a fresh SQLite file in pytest's `tmp_path`.
2. Monkeypatches `db.DB_PATH`, `db.DATA_DIR`, and the `WEATHER_DB_PATH` env var to point at that file.
3. Resets `db._db_ready = False` so `init_db()` always re-runs from scratch.

This keeps every test fully isolated from the real `data/weather.db`.

---

## Architecture

```
User (browser / CLI)
        │
        ▼
  app.py / run_pipeline.py
        │
        ▼
  pipeline/__init__.py  ←  run_pipeline(lat, lon, label)
        │
        ├── extract.py   geocode_city(city) + fetch_weather(lat, lon)  →  raw JSON
        ├── transform.py parse_weather(data)  →  (hourly_rows, daily_rows)
        └── load.py      upsert_weather(hourly_rows, daily_rows, label)  →  SQLite
                                  │
                                  ▼
                           data/weather.db
                                  │
                                  ▼
                           query.py  →  load_hourly() / load_daily() / load_location_label()
                                  │
                                  ▼
                           app.py  →  metric cards, daily summary table, charts
```

**Key design decisions:**
- `run_pipeline(lat, lon)` is the only write path — callable from the UI, CLI, or Airflow.
- Upserts are idempotent (`INSERT OR REPLACE`). Re-fetching the same location updates rows, never duplicates.
- Streamlit reruns the full script on every interaction. SQLite is the persistence layer; no in-memory state is carried between reruns except `st.session_state`.
- `init_db()` is idempotent and safe to call on every pipeline run or query (guarded by `_db_ready` flag).

---

## Key Files

| File | Purpose |
|------|---------|
| `run_pipeline.py` | Developer CLI — geocodes a city and runs the full pipeline without the Streamlit app |
| `weather_dashboard/app.py` | Streamlit UI — sidebar, metric cards, daily summary table, Altair charts |
| `weather_dashboard/pipeline/__init__.py` | `run_pipeline(lat, lon, label)` — orchestrates Extract → Transform → Load |
| `weather_dashboard/pipeline/extract.py` | Open-Meteo forecast + geocoding API calls; defines `FetchError` |
| `weather_dashboard/pipeline/transform.py` | Parses raw API JSON into typed row tuples |
| `weather_dashboard/pipeline/load.py` | Upserts `hourly_rows` and `daily_rows` into SQLite; writes `last_location` to metadata |
| `weather_dashboard/db.py` | DB connection, schema creation, migration guard |
| `weather_dashboard/query.py` | `load_hourly()`, `load_daily()`, `load_location_label()` — read-only DataFrames from SQLite |
| `weather_dashboard/utils.py` | `degrees_to_compass(degrees)` — converts wind degrees to compass label (e.g. `→ W`) |
| `data/weather.db` | SQLite database (auto-created on first run) |

---

## Database Schema

### `hourly` table

| Column | Type | Notes |
|--------|------|-------|
| `time` | TEXT (PK) | ISO 8601 datetime string, e.g. `2024-06-25T14:00` |
| `temperature_2m` | REAL | °C |
| `apparent_temperature` | REAL | °C — perceived/feels-like temperature |
| `precipitation` | REAL | mm |
| `precipitation_probability` | REAL | % |
| `wind_speed` | REAL | km/h |
| `wind_direction` | REAL | degrees |
| `humidity` | REAL | % |
| `uv_index` | REAL | — |
| `cloud_cover` | REAL | % |

### `daily` table

| Column | Type | Notes |
|--------|------|-------|
| `date` | TEXT (PK) | ISO 8601 date string, e.g. `2024-06-25` |
| `temp_max` | REAL | °C |
| `temp_min` | REAL | °C |
| `precipitation_sum` | REAL | mm |
| `precipitation_probability_max` | REAL | % — max hourly probability for the day |
| `wind_speed_max` | REAL | km/h |
| `wind_direction_dominant` | REAL | degrees |
| `sunrise` | TEXT | ISO 8601 datetime string |
| `sunset` | TEXT | ISO 8601 datetime string |

### `metadata` table

| Column | Type | Notes |
|--------|------|-------|
| `key` | TEXT (PK) | — |
| `value` | TEXT | — |

Currently stores one key: `last_location` (the display label for the last fetched city, shown in the UI header).

### DB path

Default: `data/weather.db` (relative to the project root). Override with the `WEATHER_DB_PATH` environment variable:

```bash
WEATHER_DB_PATH=/tmp/test.db poetry run streamlit run weather_dashboard/app.py
```

### Migration guard

`init_db()` in `db.py` uses a module-level `_db_ready` flag so migrations only run once per process. On each call, it:
1. Creates tables with `CREATE TABLE IF NOT EXISTS`.
2. Checks existing columns via `PRAGMA table_info(table)`.
3. Issues `ALTER TABLE … ADD COLUMN` for any missing columns.

This allows old databases to be upgraded automatically when new columns are added. **When adding a new column:** add it to both the `CREATE TABLE` statement and the `ALTER TABLE` migration guard in `init_db()`.

---

## API Layer

### Geocoding

- **Endpoint:** `https://geocoding-api.open-meteo.com/v1/search`
- **Function:** `geocode_city(city: str) -> list[dict]` in `extract.py`
- **Returns:** Up to 15 dicts with keys `lat`, `lon`, `label` (e.g. `"Berlin, Berlin, Germany"`)
- **Filter:** Results whose `name` field does not contain the search term (case-insensitive) are discarded — this removes fuzzy/alias matches unrelated to the query.
- **Raises:** `ValueError` if no results; `FetchError` on network/HTTP failure.

### Weather forecast

- **Endpoint:** `https://api.open-meteo.com/v1/forecast`
- **Function:** `fetch_weather(latitude: float, longitude: float) -> dict` in `extract.py`
- **Raises:** `FetchError` on network/HTTP failure; `ValueError` if the response is missing `hourly` or `daily` keys.

**Requested API field names vs. internal column names:**

| API field (raw) | Internal column | Table |
|-----------------|-----------------|-------|
| `temperature_2m` | `temperature_2m` | hourly |
| `apparent_temperature` | `apparent_temperature` | hourly |
| `precipitation` | `precipitation` | hourly |
| `precipitation_probability` | `precipitation_probability` | hourly |
| `windspeed_10m` | `wind_speed` | hourly |
| `winddirection_10m` | `wind_direction` | hourly |
| `relativehumidity_2m` | `humidity` | hourly |
| `uv_index` | `uv_index` | hourly |
| `cloudcover` | `cloud_cover` | hourly |
| `temperature_2m_max` | `temp_max` | daily |
| `temperature_2m_min` | `temp_min` | daily |
| `precipitation_sum` | `precipitation_sum` | daily |
| `precipitation_probability_max` | `precipitation_probability_max` | daily |
| `windspeed_10m_max` | `wind_speed_max` | daily |
| `winddirection_10m_dominant` | `wind_direction_dominant` | daily |
| `sunrise` | `sunrise` | daily |
| `sunset` | `sunset` | daily |

**Note:** The API uses `windspeed_10m` (no underscore before 10m) and `cloudcover` (no underscore). These differ from the internal column names `wind_speed` and `cloud_cover`. The mapping lives in `transform.py`.

---

## Core Functions

### `run_pipeline(lat, lon, label="")`
Entry point for the full ETL. Calls `init_db()`, `fetch_weather()`, `parse_weather()`, `upsert_weather()` in sequence. Safe to call from Airflow, CLI, or Streamlit. The `label` parameter (human-readable city name) is written to the `metadata` table as `last_location`.

### `geocode_city(city)`
Returns a list of matching location dicts. Called in two places: the Streamlit sidebar (user picks from results) and `run_pipeline.py` (CLI, first result is used automatically after filtering).

### `fetch_weather(latitude, longitude)`
Returns the raw API JSON dict with `hourly` and `daily` keys. All error handling (network, HTTP, missing fields) raises `FetchError` or `ValueError`.

### `parse_weather(data)`
Transforms raw API JSON into `(hourly_rows, daily_rows)` — lists of tuples ready for SQLite insertion.

### `upsert_weather(hourly_rows, daily_rows, label="")`
Writes rows to SQLite using `INSERT OR REPLACE`. Also writes `label` to `metadata.last_location`.

### `init_db()`
Creates tables and runs migration guard. Idempotent — safe to call multiple times; skips work after the first call per process via `_db_ready`.

### `load_hourly()` / `load_daily()`
Return DataFrames filtered to rows from today onwards (`WHERE time >= date('now', 'localtime')`). Past data is retained in SQLite but not returned to the UI.

### `load_location_label()`
Returns the string value of `metadata.last_location`, or empty string if not set.

### `degrees_to_compass(degrees)`
Converts a wind direction in degrees to a compass string with arrow prefix (e.g. `→ W`, `↗ NE`).

---

## Error Handling

- `FetchError` (defined in `extract.py`, re-exported from `pipeline/__init__.py`) — raised on any network or HTTP failure.
- `ValueError` — raised for bad API responses or city-not-found cases.
- Both are caught in `app.py` after `geocode_city()` and `run_pipeline()` calls, shown to the user via `st.error()` followed by `st.stop()`.
- Import `FetchError` from `weather_dashboard.pipeline` (not directly from `extract.py`).

---

## UI Layer (`app.py`)

### Streamlit session state keys

| Key | Type | Purpose |
|-----|------|---------|
| `geo_results` | `list[dict]` | Geocoding results from the last Search City click |
| `_prev_city` | `str` | Tracks the previous city input value; clears `geo_results` when it changes |

### Layout

1. **Sidebar** — city text input, Search City button, location radio (if multiple results), Fetch Weather button.
2. **Metric cards** (`st.metric`) — three rows of 4 cards:
   - *Row 1:* Max Temp, Min Temp, Apparent Temp (daily mean from hourly), Precip Probability (from `daily.precipitation_probability_max`)
   - *Row 2:* Precipitation, Wind Speed, Wind Direction, Avg Humidity (daily mean from hourly)
   - *Row 3:* Peak UV Index (daily max from hourly), Avg Cloud Cover (daily mean from hourly), Sunrise, Sunset
3. **Daily summary table** (`st.dataframe`) — 7-row table with Date, Conditions symbol, Max Temp, Min Temp, Precipitation, Precip Probability, Wind Speed.
4. **Forecast charts** (Altair) — three 2-column rows: Temperature + Precipitation, Wind Speed + Humidity, UV Index + Cloud Cover.

### Weather symbol logic (`_weather_symbol(row)` in `app.py`)

Derives a conditions emoji for the daily summary table from `precipitation_sum` and avg `cloud_cover` (merged from hourly via a `groupby` before rendering). **Precipitation takes priority over cloud cover:**

| Symbol | Condition | Rule |
|--------|-----------|------|
| 🌧️ | Heavy rain | `precipitation_sum` ≥ 5 mm |
| 🌦️ | Light rain | `precipitation_sum` ≥ 0.5 mm |
| ☀️ | Sunny | `cloud_cover` < 25% or missing |
| ⛅ | Partly cloudy | `cloud_cover` 25–59% |
| ☁️ | Cloudy | `cloud_cover` ≥ 60% |

**Do not reorder this logic.** A rainy day can still have any cloud cover reading — precipitation must be evaluated first.

### Temperature chart

Uses a long-format DataFrame (`temp_long`) combining `temp_max`, `temp_min`, and `apparent_temperature` (daily mean aggregated from hourly) so Altair can render a single chart with an automatic color legend. The `color` encoding drives the legend; `strokeDash` is conditioned on `series == "Feels Like"` to render it dashed. An invisible `mark_point` overlay layer carries the combined tooltip (all three values for a given day).

### Chart library

Charts are built with [Altair](https://altair-viz.github.io/). All charts use `use_container_width=True`. Temperature and precipitation charts use `height=350`; other charts use `height=300`. Axis styling uses `rgba(255,255,255,0.08)` grid lines to match the dark theme.

---

## Extension Guide

### Adding a new hourly weather field

1. Add the API field name to `_FORECAST_PARAMS["hourly"]` in `extract.py`.
2. Add the mapping (API name → column name) in `transform.py` (`parse_weather`).
3. Add the column to the `CREATE TABLE hourly` statement in `db.py`.
4. Add an `ALTER TABLE hourly ADD COLUMN` migration guard in `init_db()`.
5. Add the column to `load_hourly()` query if it needs filtering (it is included by default via `SELECT *`).
6. Add a metric card or chart in `app.py`.

### Adding a new daily weather field

Same steps as above but targeting `_FORECAST_PARAMS["daily"]`, the `daily` table, and `load_daily()`.

---

## Dependencies

Managed by Poetry (`pyproject.toml`). Core runtime dependencies:

| Package | Purpose |
|---------|---------|
| `requests` | HTTP calls to Open-Meteo APIs |
| `pandas` | DataFrame manipulation and SQL reads |
| `streamlit` | Web UI |
| `altair` | Declarative charts in Streamlit |