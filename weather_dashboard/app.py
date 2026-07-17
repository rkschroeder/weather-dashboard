import altair as alt
import pandas as pd
import streamlit as st
from weather_dashboard import alerts
from weather_dashboard.aggregate import aggregate_hourly
from weather_dashboard.pipeline.extract import geocode_city
from weather_dashboard.pipeline import run_pipeline, FetchError, save_alert_thresholds
from weather_dashboard.query import (
    load_hourly,
    load_daily,
    load_location_label,
    load_location_history,
    load_alert_thresholds,
)
from weather_dashboard.symbols import CONDITION_SYMBOLS, weather_symbol
from weather_dashboard.utils import degrees_to_compass, format_relative_time

st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 12px;
        padding: 16px 20px;
    }
    .welcome-card {
        background: rgba(79, 172, 254, 0.08);
        border: 1px solid rgba(79, 172, 254, 0.25);
        border-radius: 16px;
        padding: 40px 32px;
        text-align: center;
        margin: 24px 0 32px 0;
    }
    .step-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px 16px;
        text-align: center;
        height: 100%;
    }
    .footer {
        text-align: center;
        color: rgba(255,255,255,0.25);
        font-size: 0.8rem;
        margin-top: 48px;
        padding-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


def _fetch_and_rerun(lat: float, lon: float, label: str, spinner_text: str) -> None:
    with st.spinner(spinner_text):
        try:
            run_pipeline(lat, lon, label=label)
        except (ValueError, FetchError) as e:
            st.error(str(e))
            st.stop()
    st.rerun()


# ── Sidebar ──────────────────────────────────────────────────────────────────
current_label = load_location_label()

with st.sidebar:
    st.markdown("## 📍 Location")
    st.divider()

    history = load_location_history()
    if history:
        with st.expander("Recent Cities", expanded=not current_label):
            for loc in history:
                is_active = loc["label"] == current_label
                if st.button(
                    f"📍 {loc['label']}" if is_active else loc["label"],
                    key=f"hist_{loc['label']}",
                    use_container_width=True,
                    disabled=is_active,
                    type="primary" if is_active else "secondary",
                ):
                    _fetch_and_rerun(loc["lat"], loc["lon"], loc["label"], f"Fetching weather for {loc['label']}...")
                st.caption(f"Last fetched {format_relative_time(loc['last_fetched'])}")
        st.divider()

    current_thresholds = load_alert_thresholds()
    threshold_summary = (
        f"UV > {current_thresholds['uv_index']:.0f} · "
        f"Precip > {current_thresholds['precipitation_sum']:.0f}mm · "
        f"Temp > {current_thresholds['temp_max']:.0f}°C"
    )
    THRESHOLD_FIELDS = [
        ("uv_index", "Peak UV Index above", "Warn when a day's peak UV index exceeds this value."),
        ("precipitation_sum", "Precipitation (mm) above", "Warn when a day's total precipitation exceeds this many millimeters."),
        ("temp_max", "Max Temp (°C) above", "Warn when a day's max temperature exceeds this value."),
    ]
    with st.expander("⚠️ Alert Thresholds"):
        st.caption(threshold_summary)
        with st.form("threshold_form"):
            new_thresholds = {
                key: st.number_input(
                    label, value=float(current_thresholds[key]), min_value=0.0, step=1.0,
                    format="%.0f", help=help_text,
                )
                for key, label, help_text in THRESHOLD_FIELDS
            }
            col_save, col_reset = st.columns(2)
            save_clicked = col_save.form_submit_button("Save", use_container_width=True, type="primary")
            reset_clicked = col_reset.form_submit_button("Reset", use_container_width=True)
            if save_clicked:
                save_alert_thresholds(new_thresholds)
                st.rerun()
            if reset_clicked:
                save_alert_thresholds(dict(alerts.DEFAULT_THRESHOLDS))
                st.rerun()
    st.divider()

    city = st.text_input("City name", value="Berlin", placeholder="e.g. Berlin, Tokyo, New York")

    if st.session_state.get("_prev_city") != city:
        st.session_state.pop("geo_results", None)
        st.session_state["_prev_city"] = city

    if st.button("🔍 Search City", use_container_width=True):
        with st.spinner("Looking up city..."):
            try:
                st.session_state.geo_results = geocode_city(city)
            except (ValueError, FetchError) as e:
                st.error(str(e))
                st.stop()

    if "geo_results" in st.session_state:
        results = st.session_state.geo_results
        if len(results) == 1:
            selected = results[0]
            st.success(f"📌 {selected['label']}")
            st.caption(f"{selected['lat']:.4f}, {selected['lon']:.4f}")
        else:
            labels = [r["label"] for r in results]
            choice = st.radio(f"{len(results)} matches — select one:", labels)
            selected = results[labels.index(choice)]

        if st.button("⬇️ Fetch Weather", use_container_width=True, type="primary"):
            _fetch_and_rerun(selected["lat"], selected["lon"], selected["label"], "Fetching weather data...")

    st.divider()
    st.caption("Powered by [Open-Meteo](https://open-meteo.com/) · Free, no API key required")

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown("# 🌤️ 7-Day Weather Forecast")

daily = load_daily()
hourly = load_hourly()

if daily.empty:
    st.markdown("""
    <div class="welcome-card">
        <div style="font-size: 3rem; margin-bottom: 12px;">🌍</div>
        <h2 style="margin-bottom: 8px;">Welcome to Weather Dashboard</h2>
        <p style="color: rgba(255,255,255,0.55); font-size: 1.05rem; max-width: 480px; margin: 0 auto;">
            No forecast data yet. Use the sidebar to search for a city and fetch your first 7-day forecast.
        </p>
    </div>
    """, unsafe_allow_html=True)

    STEPS = [
        ("1️⃣", "Enter a city", "Type any city name in the sidebar on the left. The default is <em>Berlin</em>."),
        ("2️⃣", "Search the city", "Click <em>Search City</em>. If multiple locations match, select the correct one from the list."),
        ("3️⃣", "Fetch the forecast", "Click <em>Fetch Weather</em> to load the 7-day forecast. Data is saved locally for fast reloads."),
    ]
    for col, (emoji, title, text) in zip(st.columns(3, gap="medium"), STEPS):
        with col:
            st.markdown(f"""
            <div class="step-card">
                <div style="font-size: 2rem; margin-bottom: 12px;">{emoji}</div>
                <strong>{title}</strong>
                <p style="color: rgba(255,255,255,0.5); font-size: 0.9rem; margin-top: 8px;">
                    {text}
                </p>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

location_label = load_location_label() or city
current_loc = next((h for h in history if h["label"] == current_label), None)

header_col, refresh_col = st.columns([5, 1])
with header_col:
    caption = f"Showing forecast for **{location_label}**"
    if current_loc and current_loc.get("last_fetched"):
        caption += f" · updated {format_relative_time(current_loc['last_fetched'])}"
    st.caption(caption)
with refresh_col:
    if current_loc and st.button("🔄 Refresh", use_container_width=True):
        _fetch_and_rerun(current_loc["lat"], current_loc["lon"], location_label, f"Refreshing {location_label}...")
st.divider()

# ── Today's metrics ───────────────────────────────────────────────────────────
today = daily.iloc[0]

def _today_metric(hourly: pd.DataFrame, column: str, how: str):
    # Anchored on today["date"] (the location's own current day, per load_daily()'s
    # offset-aware cutoff) rather than the machine's clock — see #32.
    per_day = aggregate_hourly(hourly, column, how)
    match = per_day[per_day["date"] == today["date"]]
    return match[column].iloc[0] if not match.empty else None

def _fmt(value, spec: str = "{:.1f}") -> str:
    return spec.format(value) if pd.notna(value) else "—"

current_humidity = _today_metric(hourly, "humidity", "mean")
current_uv = _today_metric(hourly, "uv_index", "max")
current_cloud_cover = _today_metric(hourly, "cloud_cover", "mean")
current_apparent_temp = _today_metric(hourly, "apparent_temperature", "mean")

st.subheader("Today at a Glance")

# Row 1: Temperatures + precipitation probability
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Max Temp (°C)", f"{today['temp_max']:.1f}")
col2.metric("❄️ Min Temp (°C)", f"{today['temp_min']:.1f}")
col3.metric("🌡️ Apparent Temp (°C)", _fmt(current_apparent_temp))
precip_prob = today["precipitation_probability_max"] if "precipitation_probability_max" in today.index else None
col4.metric("🌂 Precip Probability (%)", f"{precip_prob:.0f}" if precip_prob is not None and pd.notna(precip_prob) else "—")

# Row 2: Precipitation + wind + humidity
col5, col6, col7, col8 = st.columns(4)
col5.metric("🌧️ Precipitation (mm)", f"{today['precipitation_sum']:.1f}")
col6.metric("💨 Wind Speed (km/h)", _fmt(today["wind_speed_max"]))
col7.metric("🧭 Wind Direction", degrees_to_compass(today["wind_direction_dominant"]) if pd.notna(today["wind_direction_dominant"]) else "—")
col8.metric("💧 Avg Humidity (%)", _fmt(current_humidity, "{:.0f}"))

# Row 3: UV + cloud cover + sunrise/sunset
col9, col10, col11, col12 = st.columns(4)
col9.metric("☀️ Peak UV Index", _fmt(current_uv))
col10.metric("☁️ Avg Cloud Cover (%)", _fmt(current_cloud_cover, "{:.0f}"))
if "sunrise" in today.index and pd.notna(today["sunrise"]):
    col11.metric("🌅 Sunrise", today["sunrise"][11:16])
    col12.metric("🌇 Sunset", today["sunset"][11:16])

st.divider()

# ── Daily Summary table ────────────────────────────────────────────────────────
summary_header_col, legend_col = st.columns([5, 1])
with summary_header_col:
    st.subheader("📋 Weekly Summary")
with legend_col:
    with st.popover("ℹ️ Symbols", use_container_width=True):
        st.markdown("**What the conditions symbols mean:**")
        for symbol, label, rule in CONDITION_SYMBOLS:
            st.markdown(f"{symbol} &nbsp;**{label}** — {rule}")

summary = daily.copy()

# Derive per-day avg cloud cover for the weather symbol
cloud_per_day = aggregate_hourly(hourly, "cloud_cover", "mean")
if cloud_per_day.empty:
    summary["cloud_cover"] = None
else:
    summary = summary.merge(cloud_per_day, on="date", how="left")

summary = alerts.merge_uv_into_daily(summary, hourly)
thresholds = load_alert_thresholds()
triggered_alerts = alerts.detect_alerts(summary, thresholds)

summary["conditions"] = summary.apply(
    lambda row: weather_symbol(row["precipitation_sum"], row["cloud_cover"]), axis=1
)
summary["date"] = summary["date"].dt.strftime("%a %d")

display_cols = {
    "date": "Date",
    "conditions": "Conditions",
    "temp_max": "Max (°C)",
    "temp_min": "Min (°C)",
    "precipitation_sum": "Precip (mm)",
    "precipitation_probability_max": "Precip Prob (%)",
    "wind_speed_max": "Wind (km/h)",
    "uv_index": "Peak UV",
}
visible_cols = {k: v for k, v in display_cols.items() if k in summary.columns}

NUMERIC_COLUMN_HELP = {
    "Max (°C)": "Daily maximum temperature",
    "Min (°C)": "Daily minimum temperature",
    "Precip (mm)": "Total precipitation for the day",
    "Precip Prob (%)": "Maximum hourly precipitation probability",
    "Wind (km/h)": "Maximum wind speed for the day",
    "Peak UV": "Peak hourly UV index for the day",
}
# column_config formatting always takes precedence over the Styler applied below —
# that's why alerts.style_exceeding only ever sets colors, and whole-number rounding
# is done here via NumberColumn(format="%.0f") instead.
summary_column_config = {
    "Date": st.column_config.TextColumn("Date", pinned=True),
    "Conditions": st.column_config.TextColumn("Conditions", width="small"),
}
for col_label, help_text in NUMERIC_COLUMN_HELP.items():
    if col_label in visible_cols.values():
        summary_column_config[col_label] = st.column_config.NumberColumn(
            col_label, help=help_text, format="%.0f"
        )

if triggered_alerts:
    count = len(triggered_alerts)
    st.warning(
        f"**⚠️ {count} threshold alert{'s' if count != 1 else ''}:**\n\n"
        + "\n".join(f"- {alert['message']}" for alert in triggered_alerts)
    )
else:
    st.success("✅ No thresholds exceeded this week.")

st.dataframe(
    summary[list(visible_cols)].rename(columns=visible_cols)
        .style.apply(alerts.style_exceeding, thresholds=thresholds, axis=1),
    use_container_width=True,
    hide_index=True,
    column_config=summary_column_config,
)

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
date_axis = alt.Axis(format="%a %d", tickCount="day", labelAngle=-30, title=None)
y_axis = alt.Axis(grid=True, gridColor="rgba(255,255,255,0.08)")

def _daily_line_chart(hourly, column, how, mark, y_title, tooltip_title, tooltip_format, y_domain=None, **mark_kwargs):
    data = aggregate_hourly(hourly, column, how)
    y_kwargs = {"scale": alt.Scale(domain=y_domain)} if y_domain else {}
    return (
        getattr(alt.Chart(data), mark)(**mark_kwargs)
        .encode(
            x=alt.X("date:T", axis=date_axis),
            y=alt.Y(f"{column}:Q", title=y_title, axis=y_axis, **y_kwargs),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%a %d"),
                alt.Tooltip(f"{column}:Q", title=tooltip_title, format=tooltip_format),
            ],
        )
        .properties(height=300)
    )

# Row A: Temperature (band + lines) | Precipitation
col_left, col_right = st.columns(2, gap="large")

with col_left:
    # Merge apparent temperature into daily so we can use a single combined tooltip
    apparent_temp_daily = aggregate_hourly(hourly, "apparent_temperature", "mean")
    if apparent_temp_daily.empty:
        daily_temp = daily.copy()
    else:
        daily_temp = daily.merge(apparent_temp_daily, on="date", how="left")

    # Long format for lines + automatic color legend
    melt_vars = ["temp_max", "temp_min"] + (["apparent_temperature"] if "apparent_temperature" in daily_temp.columns else [])
    temp_long = daily_temp[["date"] + melt_vars].melt("date", var_name="series", value_name="temperature")
    temp_long["series"] = temp_long["series"].map({
        "temp_max": "Max Temp",
        "temp_min": "Min Temp",
        "apparent_temperature": "Feels Like",
    })

    color_domain = ["Max Temp", "Min Temp", "Feels Like"]
    color_range  = ["#FF6B6B", "#60A5FA", "#FBBF24"]

    band = alt.Chart(daily_temp).mark_area(opacity=0.1).encode(
        x=alt.X("date:T", axis=date_axis),
        y=alt.Y("temp_min:Q", title="°C", axis=y_axis),
        y2=alt.Y2("temp_max"),
        color=alt.value("#4FACFE"),
    )

    lines = (
        alt.Chart(temp_long)
        .mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(filled=True, size=55))
        .encode(
            x=alt.X("date:T", axis=date_axis),
            y=alt.Y("temperature:Q", title="°C", axis=y_axis),
            color=alt.Color(
                "series:N",
                scale=alt.Scale(domain=color_domain, range=color_range),
                legend=alt.Legend(orient="bottom", title=None, labelFontSize=12, symbolSize=100, direction="horizontal"),
            ),
            strokeDash=alt.condition(
                alt.datum.series == "Feels Like",
                alt.value([5, 3]),
                alt.value([0]),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%A, %b %d"),
                alt.Tooltip("series:N", title=""),
                alt.Tooltip("temperature:Q", title="°C", format=".1f"),
            ],
        )
    )

    # Invisible overlay to show all three values in one tooltip on hover
    combined_tt = [alt.Tooltip("date:T", title="Date", format="%A, %b %d"),
                   alt.Tooltip("temp_max:Q", title="Max (°C)", format=".1f"),
                   alt.Tooltip("temp_min:Q", title="Min (°C)", format=".1f")]
    if "apparent_temperature" in daily_temp.columns:
        combined_tt.append(alt.Tooltip("apparent_temperature:Q", title="Feels Like (°C)", format=".1f"))
    overlay = (
        alt.Chart(daily_temp)
        .mark_point(opacity=0, size=400)
        .encode(x=alt.X("date:T"), y=alt.Y("temp_max:Q"), tooltip=combined_tt)
    )

    temp_chart = alt.layer(band, lines, overlay).properties(height=350)
    st.subheader("🌡️ Temperature (°C)")
    st.altair_chart(temp_chart, use_container_width=True)

with col_right:
    max_precip = float(daily["precipitation_sum"].max()) if not daily.empty else 10
    precip_chart = (
        alt.Chart(daily)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("date:T", axis=date_axis),
            y=alt.Y("precipitation_sum:Q", title="Precipitation (mm)", axis=y_axis),
            color=alt.Color(
                "precipitation_sum:Q",
                scale=alt.Scale(scheme="blues", domain=[0, max(max_precip, 1)]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%A, %b %d"),
                alt.Tooltip("precipitation_sum:Q", title="Precipitation (mm)", format=".1f"),
                alt.Tooltip("precipitation_probability_max:Q", title="Precip Probability (%)", format=".0f"),
            ],
        )
        .properties(height=350)
    )
    st.subheader("🌧️ Precipitation (mm)")
    st.altair_chart(precip_chart, use_container_width=True)

# Row B: Wind Speed | Humidity
wind_chart = _daily_line_chart(hourly, "wind_speed", "mean", "mark_line", "km/h", "Wind Speed (km/h)", ".1f")

col_left, col_right = st.columns(2, gap="large")
with col_left:
    st.subheader("💨 Wind Speed Forecast (km/h)")
    st.altair_chart(wind_chart, use_container_width=True)

with col_right:
    if "humidity" in hourly.columns:
        humidity_chart = _daily_line_chart(
            hourly, "humidity", "mean", "mark_line", "%", "Humidity (%)", ".0f", y_domain=[0, 100]
        )
        st.subheader("💧 Humidity Forecast (%)")
        st.altair_chart(humidity_chart, use_container_width=True)

# Row C: Peak UV Index | Cloud Cover
if "uv_index" in hourly.columns or "cloud_cover" in hourly.columns:
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        if "uv_index" in hourly.columns:
            uv_chart = _daily_line_chart(
                hourly, "uv_index", "max", "mark_line", "UV Index", "Peak UV Index", ".1f", y_domain=[0, 11]
            )
            st.subheader("☀️ Peak UV Index Forecast")
            st.altair_chart(uv_chart, use_container_width=True)

    with col_right:
        if "cloud_cover" in hourly.columns:
            cloud_chart = _daily_line_chart(
                hourly, "cloud_cover", "mean", "mark_area", "%", "Cloud Cover (%)", ".0f",
                y_domain=[0, 100], opacity=0.5,
            )
            st.subheader("☁️ Cloud Cover Forecast (%)")
            st.altair_chart(cloud_chart, use_container_width=True)

st.divider()

st.markdown("""
<div class="footer">
    Data from <a href="https://open-meteo.com/" style="color: rgba(255,255,255,0.4);">Open-Meteo</a>
    · Free & open-source weather API
</div>
""", unsafe_allow_html=True)