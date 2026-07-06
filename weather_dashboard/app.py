import altair as alt
import pandas as pd
import streamlit as st
from weather_dashboard import alerts
from weather_dashboard.pipeline.extract import geocode_city
from weather_dashboard.pipeline import run_pipeline, FetchError, save_alert_thresholds
from weather_dashboard.query import (
    load_hourly,
    load_daily,
    load_location_label,
    load_location_history,
    load_alert_thresholds,
)
from weather_dashboard.utils import degrees_to_compass

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

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📍 Location")
    st.divider()

    history = load_location_history()
    if history:
        with st.expander("Recent Cities", expanded=True):
            for loc in history:
                if st.button(loc["label"], key=f"hist_{loc['label']}", use_container_width=True):
                    with st.spinner(f"Fetching weather for {loc['label']}..."):
                        try:
                            run_pipeline(loc["lat"], loc["lon"], label=loc["label"])
                        except (ValueError, FetchError) as e:
                            st.error(str(e))
                            st.stop()
                    st.rerun()
        st.divider()

    current_thresholds = load_alert_thresholds()
    with st.expander("⚠️ Alert Thresholds"):
        with st.form("threshold_form"):
            uv_threshold = st.number_input(
                "Peak UV Index above", value=float(current_thresholds["uv_index"]), min_value=0.0, step=0.5
            )
            precip_threshold = st.number_input(
                "Precipitation (mm) above", value=float(current_thresholds["precipitation_sum"]), min_value=0.0, step=0.5
            )
            temp_threshold = st.number_input(
                "Max Temp (°C) above", value=float(current_thresholds["temp_max"]), min_value=0.0, step=0.5
            )
            if st.form_submit_button("Save Thresholds", use_container_width=True):
                save_alert_thresholds({
                    "uv_index": uv_threshold,
                    "precipitation_sum": precip_threshold,
                    "temp_max": temp_threshold,
                })
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
            with st.spinner("Fetching weather data..."):
                try:
                    run_pipeline(selected["lat"], selected["lon"], label=selected["label"])
                except (ValueError, FetchError) as e:
                    st.error(str(e))
                    st.stop()
            st.success(f"Updated for {selected['label']}.")

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

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown("""
        <div class="step-card">
            <div style="font-size: 2rem; margin-bottom: 12px;">1️⃣</div>
            <strong>Enter a city</strong>
            <p style="color: rgba(255,255,255,0.5); font-size: 0.9rem; margin-top: 8px;">
                Type any city name in the sidebar on the left. The default is <em>Berlin</em>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="step-card">
            <div style="font-size: 2rem; margin-bottom: 12px;">2️⃣</div>
            <strong>Search the city</strong>
            <p style="color: rgba(255,255,255,0.5); font-size: 0.9rem; margin-top: 8px;">
                Click <em>Search City</em>. If multiple locations match, select the correct one from the list.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="step-card">
            <div style="font-size: 2rem; margin-bottom: 12px;">3️⃣</div>
            <strong>Fetch the forecast</strong>
            <p style="color: rgba(255,255,255,0.5); font-size: 0.9rem; margin-top: 8px;">
                Click <em>Fetch Weather</em> to load the 7-day forecast. Data is saved locally for fast reloads.
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

location_label = load_location_label() or city
st.caption(f"Showing forecast for **{location_label}**")
st.divider()

# ── Today's metrics ───────────────────────────────────────────────────────────
today = daily.iloc[0]

today_date = pd.Timestamp.now().normalize()
current_humidity = None
if not hourly.empty and "humidity" in hourly.columns:
    today_hourly = hourly[hourly["time"].dt.normalize() == today_date]
    if not today_hourly.empty:
        current_humidity = today_hourly["humidity"].mean()

current_uv = None
if not hourly.empty and "uv_index" in hourly.columns:
    today_hourly_uv = hourly[hourly["time"].dt.normalize() == today_date]
    if not today_hourly_uv.empty:
        current_uv = today_hourly_uv["uv_index"].max()

current_cloud_cover = None
if not hourly.empty and "cloud_cover" in hourly.columns:
    today_hourly_cc = hourly[hourly["time"].dt.normalize() == today_date]
    if not today_hourly_cc.empty:
        current_cloud_cover = today_hourly_cc["cloud_cover"].mean()

current_apparent_temp = None
if not hourly.empty and "apparent_temperature" in hourly.columns:
    today_hourly_at = hourly[hourly["time"].dt.normalize() == today_date]
    if not today_hourly_at.empty:
        current_apparent_temp = today_hourly_at["apparent_temperature"].mean()

st.subheader("Today at a Glance")

# Row 1: Temperatures + precipitation probability
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Max Temp (°C)", f"{today['temp_max']:.1f}")
col2.metric("❄️ Min Temp (°C)", f"{today['temp_min']:.1f}")
col3.metric("🌡️ Apparent Temp (°C)", f"{current_apparent_temp:.1f}" if pd.notna(current_apparent_temp) else "—")
precip_prob = today["precipitation_probability_max"] if "precipitation_probability_max" in today.index else None
col4.metric("🌂 Precip Probability (%)", f"{precip_prob:.0f}" if precip_prob is not None and pd.notna(precip_prob) else "—")

# Row 2: Precipitation + wind + humidity
col5, col6, col7, col8 = st.columns(4)
col5.metric("🌧️ Precipitation (mm)", f"{today['precipitation_sum']:.1f}")
col6.metric("💨 Wind Speed (km/h)", f"{today['wind_speed_max']:.1f}" if pd.notna(today["wind_speed_max"]) else "—")
col7.metric("🧭 Wind Direction", degrees_to_compass(today["wind_direction_dominant"]) if pd.notna(today["wind_direction_dominant"]) else "—")
col8.metric("💧 Avg Humidity (%)", f"{current_humidity:.0f}" if pd.notna(current_humidity) else "—")

# Row 3: UV + cloud cover + sunrise/sunset
col9, col10, col11, col12 = st.columns(4)
col9.metric("☀️ Peak UV Index", f"{current_uv:.1f}" if pd.notna(current_uv) else "—")
col10.metric("☁️ Avg Cloud Cover (%)", f"{current_cloud_cover:.0f}" if pd.notna(current_cloud_cover) else "—")
if "sunrise" in today.index and pd.notna(today["sunrise"]):
    col11.metric("🌅 Sunrise", today["sunrise"][11:16])
    col12.metric("🌇 Sunset", today["sunset"][11:16])

st.divider()

# ── Daily Summary table ────────────────────────────────────────────────────────
st.subheader("📋 Daily Summary")
summary = daily.copy()

# Derive per-day avg cloud cover for the weather symbol
if "cloud_cover" in hourly.columns:
    cloud_per_day = (
        hourly.assign(date=hourly["time"].dt.normalize())
        .groupby("date", as_index=False)["cloud_cover"]
        .mean()
    )
    summary = summary.merge(cloud_per_day, on="date", how="left")
else:
    summary["cloud_cover"] = None

summary = alerts.merge_uv_into_daily(summary, hourly)
thresholds = load_alert_thresholds()
triggered_alerts = alerts.detect_alerts(summary, thresholds)

def _weather_symbol(row):
    precip = row["precipitation_sum"] or 0
    cloud = row["cloud_cover"]
    if precip >= 5:
        return "🌧️"
    if precip >= 0.5:
        return "🌦️"
    if cloud is None or pd.isna(cloud):
        return "☀️"
    if cloud < 25:
        return "☀️"
    if cloud < 60:
        return "⛅"
    return "☁️"

summary["conditions"] = summary.apply(_weather_symbol, axis=1)
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

for alert in triggered_alerts:
    st.warning(alert["message"])

st.dataframe(
    summary[list(visible_cols)].rename(columns=visible_cols)
        .style.apply(alerts.style_exceeding, thresholds=thresholds, axis=1),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
date_axis = alt.Axis(format="%a %d", tickCount="day", labelAngle=-30, title=None)
y_axis = alt.Axis(grid=True, gridColor="rgba(255,255,255,0.08)")

# Row A: Temperature (band + lines) | Precipitation
col_left, col_right = st.columns(2, gap="large")

with col_left:
    # Merge apparent temperature into daily so we can use a single combined tooltip
    if "apparent_temperature" in hourly.columns and not hourly.empty:
        apparent_temp_daily = (
            hourly.assign(date=hourly["time"].dt.normalize())
            .groupby("date", as_index=False)["apparent_temperature"]
            .mean()
        )
        daily_temp = daily.merge(apparent_temp_daily, on="date", how="left")
    else:
        daily_temp = daily.copy()

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
wind_avg = (
    hourly.assign(date=hourly["time"].dt.normalize())
    .groupby("date", as_index=False)["wind_speed"]
    .mean()
)
wind_chart = (
    alt.Chart(wind_avg)
    .mark_line()
    .encode(
        x=alt.X("date:T", axis=date_axis),
        y=alt.Y("wind_speed:Q", title="km/h", axis=y_axis),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%a %d"),
            alt.Tooltip("wind_speed:Q", title="Wind Speed (km/h)", format=".1f"),
        ],
    )
    .properties(height=300)
)

col_left, col_right = st.columns(2, gap="large")
with col_left:
    st.subheader("💨 Wind Speed Forecast (km/h)")
    st.altair_chart(wind_chart, use_container_width=True)

with col_right:
    if "humidity" in hourly.columns:
        humidity_avg = (
            hourly.assign(date=hourly["time"].dt.normalize())
            .groupby("date", as_index=False)["humidity"]
            .mean()
        )
        humidity_chart = (
            alt.Chart(humidity_avg)
            .mark_line()
            .encode(
                x=alt.X("date:T", axis=date_axis),
                y=alt.Y("humidity:Q", title="%", scale=alt.Scale(domain=[0, 100]), axis=y_axis),
                tooltip=[
                    alt.Tooltip("date:T", title="Date", format="%a %d"),
                    alt.Tooltip("humidity:Q", title="Humidity (%)", format=".0f"),
                ],
            )
            .properties(height=300)
        )
        st.subheader("💧 Humidity Forecast (%)")
        st.altair_chart(humidity_chart, use_container_width=True)

# Row C: Peak UV Index | Cloud Cover
if "uv_index" in hourly.columns or "cloud_cover" in hourly.columns:
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        if "uv_index" in hourly.columns:
            uv_daily = (
                hourly.assign(date=hourly["time"].dt.normalize())
                .groupby("date", as_index=False)["uv_index"]
                .max()
            )
            uv_chart = (
                alt.Chart(uv_daily)
                .mark_line()
                .encode(
                    x=alt.X("date:T", axis=date_axis),
                    y=alt.Y("uv_index:Q", title="UV Index", scale=alt.Scale(domain=[0, 11]), axis=y_axis),
                    tooltip=[
                        alt.Tooltip("date:T", title="Date", format="%a %d"),
                        alt.Tooltip("uv_index:Q", title="Peak UV Index", format=".1f"),
                    ],
                )
                .properties(height=300)
            )
            st.subheader("☀️ Peak UV Index Forecast")
            st.altair_chart(uv_chart, use_container_width=True)

    with col_right:
        if "cloud_cover" in hourly.columns:
            cloud_daily = (
                hourly.assign(date=hourly["time"].dt.normalize())
                .groupby("date", as_index=False)["cloud_cover"]
                .mean()
            )
            cloud_chart = (
                alt.Chart(cloud_daily)
                .mark_area(opacity=0.5)
                .encode(
                    x=alt.X("date:T", axis=date_axis),
                    y=alt.Y("cloud_cover:Q", title="%", scale=alt.Scale(domain=[0, 100]), axis=y_axis),
                    tooltip=[
                        alt.Tooltip("date:T", title="Date", format="%a %d"),
                        alt.Tooltip("cloud_cover:Q", title="Cloud Cover (%)", format=".0f"),
                    ],
                )
                .properties(height=300)
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