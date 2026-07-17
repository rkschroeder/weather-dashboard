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
- Sidebar: Recent Cities expander (one-click reload from SQLite `locations` table; pinned/disabled button + "last fetched" relative-time caption for the active city), Alert Thresholds expander (editable UV/precipitation/temperature thresholds, persisted to SQLite, displayed and edited as whole numbers; collapsed summary caption; Reset-to-defaults button), city search, geocode results picker, Fetch Weather button
- Header row: current location + last-updated relative-time caption, with a Refresh button to re-fetch the active location
- Metric cards — 3 rows of 4:
  - Temperatures: Max Temp, Min Temp, Apparent Temp, Precip Probability
  - Conditions: Precipitation, Wind Speed, Wind Direction, Humidity
  - Other: Peak UV Index, Cloud Cover, Sunrise, Sunset
- Weekly Summary table: Date, Conditions symbol, Max Temp, Min Temp, Precipitation, Precip Probability, Wind Speed, Peak UV — cells exceeding a threshold are highlighted. **All numeric columns are rounded to whole numbers for display** (via `column_config`'s `%.0f` format); the underlying stored values and threshold comparisons retain full precision. An info popover next to the table header explains what each conditions symbol means.
- Threshold alerts: a single grouped warning banner lists all triggered day/metric combinations (or a success message if none are triggered), above the Weekly Summary table. Alert messages also round values to whole numbers, matching the table and the threshold inputs.
- Forecast charts (Altair, 2-column layout):
  - Temperature: shaded band + Max/Min/Feels Like lines with color legend and point markers
  - Precipitation: intensity-gradient bars (blue scale by mm)
  - Wind Speed | Humidity
  - Peak UV Index | Cloud Cover

---

## Next Steps

Potential improvements roughly in priority order:

1. **Hourly forecast view** — current charts aggregate hourly data to daily; add a toggle or separate section showing true hourly detail (e.g. hourly temperature curve for today)
2. **Wind chill / heat index** — derive and display alongside apparent temperature for more context
3. **Snowfall field** — add `snowfall` and `snowfall_sum` from Open-Meteo (same extension pattern as existing fields)
4. **CSV export** — add a download button (`st.download_button`) for the daily summary DataFrame
5. **Multi-city comparison** — allow fetching multiple cities and overlaying them on the same chart
6. **Deploy to Streamlit Cloud** — add `requirements.txt` export (`poetry export`) and `secrets.toml` stub, document deployment steps
7. **Automated refresh** — schedule the pipeline via Airflow or a simple cron job so data stays fresh without manual Fetch clicks. The threshold-alerts detection logic in `alerts.py` has no Streamlit/UI dependency by design, so a future Airflow task can reuse `detect_alerts()`'s message strings directly as an email body.

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

75 unit tests, all passing. No external services or live network calls — HTTP is mocked via `unittest.mock.patch` and each DB-touching test uses an isolated SQLite file via the `tmp_db` fixture in `conftest.py`.

### Test modules

| File | Covers |
|------|--------|
| `tests/conftest.py` | `tmp_db` fixture (redirects `DB_PATH` to a temp file, resets `_db_ready` between tests); `SAMPLE_API_PAYLOAD` shared fixture |
| `tests/test_utils.py` | `degrees_to_compass` — all cardinal/intercardinal directions, boundary rounding, 360° wrap-around |
| `tests/test_transform.py` | `parse_weather` — correct field order, empty arrays, missing key raises `ValueError` |
| `tests/test_extract.py` | `geocode_city` / `fetch_weather` — success, fuzzy-match filter, no-results, network errors, HTTP errors |
| `tests/test_db.py` | `init_db` — creates all 4 tables, idempotency, migration guard adds missing columns to existing DB (including `locations`) |
| `tests/test_load.py` | `upsert_weather` — inserts rows, upsert replaces on PK conflict, label written/overwritten/skipped, location row written/skipped, `location_utc_offset` written/overwritten/skipped; `save_alert_thresholds` — writes and overwrites the `alert_thresholds` metadata row |
| `tests/test_query.py` | `load_hourly` / `load_daily` / `load_location_label` / `load_location_history` — DataFrame columns, past-row filter, empty-table default, ordering, limit; `_location_cutoff_date` — computes "today" from a location's UTC offset rather than the machine's timezone; `load_alert_thresholds` — defaults when unset, merges partial saved config, round-trips a full config |
| `tests/test_pipeline.py` | `run_pipeline` — ETL call order and arguments, default label, `FetchError` propagation |
| `tests/test_alerts.py` | `merge_uv_into_daily` — per-day peak UV merge, missing-column fallback; `detect_alerts` — strict `>` threshold comparison, message format, empty DataFrame |
| `tests/test_aggregate.py` | `aggregate_hourly` — per-day mean/max aggregation, empty-but-correctly-shaped return for empty input or a missing column |
| `tests/test_symbols.py` | `weather_symbol` — all 5 condition outcomes, precipitation-priority-over-cloud-cover ordering, missing/NaN cloud cover falling back to sunny |

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
        └── load.py      upsert_weather(hourly_rows, daily_rows, lat, lon, label, utc_offset_seconds)  →  SQLite
                                  │
                                  ▼
                           data/weather.db  (hourly, daily, metadata, locations)
                                  │
                                  ▼
                           query.py  →  load_hourly() / load_daily() / load_location_label() / load_location_history() / load_alert_thresholds()
                                  │
                                  ▼
                           app.py  →  metric cards, weekly summary table, charts
                                  │
                                  ▼
                           alerts.py  →  merge_uv_into_daily() / detect_alerts() / style_exceeding()
```

**Key design decisions:**
- `run_pipeline(lat, lon)` is the only write path — callable from the UI, CLI, or Airflow.
- Upserts are idempotent (`INSERT OR REPLACE`). Re-fetching the same location updates rows, never duplicates.
- Streamlit reruns the full script on every interaction. SQLite is the persistence layer; no in-memory state is carried between reruns except `st.session_state`.
- `init_db()` is idempotent and safe to call on every pipeline run or query (guarded by `_db_ready` flag).
- `alerts.py` has zero Streamlit or DB dependency — it's pure pandas logic operating on DataFrames, so it's reusable from the UI, a script, or (in the future) an Airflow task, the same way `run_pipeline()` is.

---

## Key Files

| File | Purpose |
|------|---------|
| `run_pipeline.py` | Developer CLI — geocodes a city and runs the full pipeline without the Streamlit app |
| `weather_dashboard/app.py` | Streamlit UI — sidebar, metric cards, weekly summary table, Altair charts |
| `weather_dashboard/pipeline/__init__.py` | `run_pipeline(lat, lon, label)` — orchestrates Extract → Transform → Load |
| `weather_dashboard/pipeline/extract.py` | Open-Meteo forecast + geocoding API calls; defines `FetchError` |
| `weather_dashboard/pipeline/transform.py` | Parses raw API JSON into typed row tuples |
| `weather_dashboard/pipeline/load.py` | Upserts `hourly_rows` and `daily_rows` into SQLite; writes `last_location` and `location_utc_offset` to metadata and city to `locations`; `save_alert_thresholds()` writes threshold config to metadata |
| `weather_dashboard/db.py` | DB connection, schema creation, `_ensure_column` migration helper |
| `weather_dashboard/query.py` | `load_hourly()`, `load_daily()`, `load_location_label()`, `load_location_history()`, `load_alert_thresholds()` — read-only from SQLite |
| `weather_dashboard/alerts.py` | `merge_uv_into_daily()`, `detect_alerts()`, `style_exceeding()` — pure pandas threshold-alert logic, no Streamlit/DB dependency |
| `weather_dashboard/aggregate.py` | `aggregate_hourly(hourly, column, how)` — shared hourly→daily groupby helper, pure pandas, no Streamlit/DB dependency; used by `app.py`, `alerts.py`, and `run_pipeline.py` |
| `weather_dashboard/symbols.py` | `weather_symbol(precipitation_sum, cloud_cover)`, `CONDITION_SYMBOLS` — pure conditions-emoji logic, no Streamlit/DB dependency; used by `app.py`'s Weekly Summary table and its info popover legend |
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

Stores three keys: `last_location` (the display label for the last fetched city, shown in the UI header), `location_utc_offset` (the last fetched city's UTC offset in seconds, from the API's `utc_offset_seconds` — used by `load_hourly()`/`load_daily()` to compute "today" in that city's own timezone rather than the machine's), and `alert_thresholds` (JSON-encoded dict of threshold overrides, e.g. `{"uv_index": 7.0, "precipitation_sum": 10.0, "temp_max": 35.0}` — written by `save_alert_thresholds()`, read by `load_alert_thresholds()` which merges it over `alerts.DEFAULT_THRESHOLDS`).

### `locations` table

| Column | Type | Notes |
|--------|------|-------|
| `label` | TEXT (PK) | Display name, e.g. `"Berlin, Berlin, Germany"` |
| `lat` | REAL | Latitude |
| `lon` | REAL | Longitude |
| `last_fetched` | TEXT | SQLite `datetime('now')` timestamp, updated on each fetch |

Populated by `upsert_weather` whenever `label`, `lat`, and `lon` are all provided. Used by `load_location_history()` to render the Recent Cities sidebar section.

### DB path

Default: `data/weather.db` (relative to the project root). Override with the `WEATHER_DB_PATH` environment variable:

```bash
WEATHER_DB_PATH=/tmp/test.db poetry run streamlit run weather_dashboard/app.py
```

### Migration guard

`init_db()` in `db.py` uses a module-level `_db_ready` flag so migrations only run once per process. On each call, it:
1. Creates tables with `CREATE TABLE IF NOT EXISTS`.
2. Calls `_ensure_column(conn, table, column, type)` for each column added after the initial schema.

`_ensure_column` checks `PRAGMA table_info(table)` and issues `ALTER TABLE … ADD COLUMN` only if the column is absent. This is needed because `ALTER TABLE` has no `IF NOT EXISTS` clause — without the check it would raise a duplicate-column error on fresh databases where the column was already created by `CREATE TABLE`.

This allows old databases to be upgraded automatically when new columns are added. **When adding a new column:** add it to the `CREATE TABLE` statement and call `_ensure_column` for it in `init_db()`.

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
Transforms raw API JSON into `(hourly_rows, daily_rows, utc_offset_seconds)` — lists of tuples ready for SQLite insertion, plus the forecast location's UTC offset (from the API's top-level `utc_offset_seconds` field, defaulting to `0` if absent).

### `upsert_weather(hourly_rows, daily_rows, lat=None, lon=None, label="", utc_offset_seconds=None)`
Writes rows to SQLite using `INSERT OR REPLACE`. Also writes `label` to `metadata.last_location` and, when provided, `utc_offset_seconds` to `metadata.location_utc_offset`. When `label`, `lat`, and `lon` are all provided, upserts a row into the `locations` table with the current timestamp.

### `init_db()`
Creates tables and runs migration guard. Idempotent — safe to call multiple times; skips work after the first call per process via `_db_ready`.

### `load_hourly()` / `load_daily()`
Return DataFrames filtered to rows from today onwards in the **forecast location's own timezone** — not the machine's. The cutoff date is computed in Python from `metadata.location_utc_offset` (defaulting to UTC if unset) and bound as a query parameter, rather than relying on SQLite's `date('now', 'localtime')` (which depends on the host machine's timezone and would disagree with the location-local timestamps `extract.py` stores via `timezone=auto`). Past data is retained in SQLite but not returned to the UI.

### `load_location_label()`
Returns the string value of `metadata.last_location`, or empty string if not set.

### `load_location_history(limit=10)`
Returns up to `limit` previously fetched locations from the `locations` table, ordered by `last_fetched` descending (most recent first). Each entry is a dict with `label`, `lat`, and `lon`.

### `degrees_to_compass(degrees)`
Converts a wind direction in degrees to a compass string with arrow prefix (e.g. `→ W`, `↗ NE`).

### `load_alert_thresholds()`
Reads the `alert_thresholds` metadata row and JSON-decodes it, merging over `alerts.DEFAULT_THRESHOLDS` so a partially-saved config still has every key. Returns `alerts.DEFAULT_THRESHOLDS` unchanged if nothing has been saved yet.

### `save_alert_thresholds(thresholds: dict)`
Writes a `{"uv_index": ..., "precipitation_sum": ..., "temp_max": ...}` dict as JSON to the `alert_thresholds` metadata row (`INSERT OR REPLACE`).

### `merge_uv_into_daily(daily, hourly)`
Adds a `uv_index` column to a copy of the daily DataFrame — the per-day max of hourly `uv_index`, via the shared `aggregate.aggregate_hourly()` helper (same helper `app.py` and `run_pipeline.py` use for their own hourly→daily aggregations). Needed because UV is only stored hourly, not in the `daily` table.

### `detect_alerts(daily_with_uv, thresholds)`
Pure function: for each day and each threshold key present in both `thresholds` and the DataFrame's columns, flags values strictly greater than (`>`) the threshold. Returns a list of `{"date", "metric", "label", "value", "threshold", "message"}` dicts — the `message` string is written to render as a `st.warning()` banner in `app.py`, and is also the reusable payload a future Airflow task would forward as an email body. No Streamlit or DB import — safe to call from a script or DAG.

### `style_exceeding(row, thresholds)`
Row function passed to `pandas.Styler.apply(axis=1)` on the *rendered* Weekly Summary DataFrame (column names like `"Max (°C)"`, not the underlying metric keys). Returns a CSS background-color string per cell that exceeds its threshold, via `alerts.DISPLAY_COLUMN_METRICS` mapping display names back to metric keys. Applied to the unrounded value — the whole-number display is a separate `column_config` concern (see Number formatting).

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

1. **Sidebar** — Recent Cities expander (collapsed once a forecast is loaded; buttons for each previously fetched city, most recent first, with the active city shown pinned/disabled and a "last fetched" relative-time caption under each entry; clicking one calls `run_pipeline` directly and reruns the page), Alert Thresholds expander (collapsed summary caption of current values; `st.form` with UV/precipitation/max-temp number inputs — whole numbers only, `format="%.0f"`, `step=1.0` — seeded from `load_alert_thresholds()`; Save button calls `save_alert_thresholds()`, Reset button restores `alerts.DEFAULT_THRESHOLDS`, both rerun), city text input, Search City button, location radio (if multiple results), Fetch Weather button.
2. **Header row** — "Showing forecast for **{location}** · updated {relative time}" caption plus a Refresh button that re-runs the pipeline for the currently loaded location.
3. **Metric cards** (`st.metric`) — three rows of 4 cards:
   - *Row 1:* Max Temp, Min Temp, Apparent Temp (daily mean from hourly), Precip Probability (from `daily.precipitation_probability_max`)
   - *Row 2:* Precipitation, Wind Speed, Wind Direction, Avg Humidity (daily mean from hourly)
   - *Row 3:* Peak UV Index (daily max from hourly), Avg Cloud Cover (daily mean from hourly), Sunrise, Sunset
4. **Alert banner** — a single grouped `st.warning()` listing every triggered threshold alert (from `alerts.detect_alerts()`), or an `st.success()` message when none are triggered; rendered above the Weekly Summary table, next to an info popover explaining the conditions symbols (`CONDITION_SYMBOLS` in `weather_dashboard/symbols.py`).
5. **Weekly Summary table** (`st.dataframe`) — 7-row table with Date, Conditions symbol, Max Temp, Min Temp, Precipitation, Precip Probability, Wind Speed, Peak UV; styled with a `pandas.Styler` (`alerts.style_exceeding`) that highlights cells exceeding their threshold in amber, plus `column_config` (`st.column_config.NumberColumn(..., format="%.0f")`) that **rounds every numeric column to a whole number for display** and adds a help tooltip per column; the Date column is pinned.
6. **Forecast charts** (Altair) — three 2-column rows: Temperature + Precipitation, Wind Speed + Humidity, UV Index + Cloud Cover.

### Number formatting

Numbers shown in the Alert Thresholds inputs/summary, the alert banner messages, and the Weekly Summary table are **rounded to the nearest whole number** for display (`%.0f`-style formatting) — e.g. a stored value of `9.2` renders as `9`. This is presentation-only: the underlying SQLite/DataFrame values keep full precision, and threshold comparisons in `detect_alerts()` and `style_exceeding()` always operate on the unrounded value. Metric cards and charts elsewhere in `app.py` are unaffected and keep their existing 1-decimal/0-decimal formatting.

### Threshold alerts (`alerts.py`, used in `app.py`)

Thresholds default to `alerts.DEFAULT_THRESHOLDS` (UV index > 7, precipitation > 10 mm, max temp > 35°C), editable via the sidebar's Alert Thresholds form (whole numbers only) and persisted to the `metadata` table (see Database Schema). On each rerun, `app.py`:
1. Merges peak UV into the daily summary DataFrame via `merge_uv_into_daily()` (UV is hourly-only otherwise).
2. Calls `detect_alerts()` to get triggered alerts, rendered as a single grouped `st.warning()` above the table (or `st.success()` if empty). Alert messages round both the value and threshold to whole numbers.
3. Applies `style_exceeding()` as a `Styler` on the displayed DataFrame to highlight exceeding cells; `column_config` separately rounds the displayed numbers (formatting from `column_config` always takes precedence over `Styler` formatting).

Comparison is strict (`>`), matching the "exceeds" wording — a value exactly equal to its threshold does not trigger.

### Weather symbol logic (`weather_symbol(precipitation_sum, cloud_cover)` in `weather_dashboard/symbols.py`)

Derives a conditions emoji for the Weekly Summary table from `precipitation_sum` and avg `cloud_cover` (merged from hourly via a `groupby` before rendering; `app.py` calls it per-row via `summary.apply(...)`). Pure function, no Streamlit/DB dependency — same reuse pattern as `alerts.py`/`aggregate.py`, and directly unit-tested in `tests/test_symbols.py`. The four thresholds (`HEAVY_RAIN_MM`, `LIGHT_RAIN_MM`, `SUNNY_MAX_CLOUD`, `PARTLY_CLOUDY_MAX_CLOUD`) are named constants that `CONDITION_SYMBOLS`' rule text is generated from, so the table, its info popover legend, and the comparison logic can't drift out of sync. **Precipitation takes priority over cloud cover:**

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
4. Call `_ensure_column(conn, "hourly", "new_column", "REAL")` in `init_db()` after the `CREATE TABLE` block.
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