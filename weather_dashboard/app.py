import altair as alt
import pandas as pd
import streamlit as st
from weather_dashboard.pipeline.extract import geocode_city
from weather_dashboard.pipeline import run_pipeline, FetchError
from weather_dashboard.query import load_hourly, load_daily, load_location_label
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

st.subheader("Today at a Glance")

col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Max Temp (°C)", f"{today['temp_max']:.1f}")
col2.metric("❄️ Min Temp (°C)", f"{today['temp_min']:.1f}")
col3.metric("🌧️ Precipitation (mm)", f"{today['precipitation_sum']:.1f}")
col4.metric("💨 Wind Speed (km/h)", f"{today['wind_speed_max']:.1f}" if today["wind_speed_max"] is not None else "—")

col5, col6, col7, col8 = st.columns(4)
col5.metric("🧭 Wind Direction", degrees_to_compass(today["wind_direction_dominant"]) if today["wind_direction_dominant"] is not None else "—")
col6.metric("💧 Avg Humidity (%)", f"{current_humidity:.0f}" if current_humidity is not None else "—")
col7.metric("☀️ Peak UV Index", f"{current_uv:.1f}" if current_uv is not None else "—")
col8.metric("☁️ Avg Cloud Cover (%)", f"{current_cloud_cover:.0f}" if current_cloud_cover is not None else "—")

if "sunrise" in today.index and pd.notna(today["sunrise"]):
    col_sr, col_ss = st.columns(2)
    col_sr.metric("🌅 Sunrise", today["sunrise"][11:16])
    col_ss.metric("🌇 Sunset", today["sunset"][11:16])

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
    "wind_speed_max": "Wind (km/h)",
}
st.dataframe(
    summary[list(display_cols)].rename(columns=display_cols),
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
    band = alt.Chart(daily).mark_area(opacity=0.15, color="#4FACFE").encode(
        x=alt.X("date:T", axis=date_axis),
        y=alt.Y("temp_min:Q", title="°C", axis=y_axis),
        y2=alt.Y2("temp_max"),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%a %d"),
            alt.Tooltip("temp_max:Q", title="Max (°C)", format=".1f"),
            alt.Tooltip("temp_min:Q", title="Min (°C)", format=".1f"),
        ],
    )
    line_max = alt.Chart(daily).mark_line(color="#4FACFE").encode(
        x=alt.X("date:T", axis=date_axis),
        y=alt.Y("temp_max:Q", title="°C"),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%a %d"),
            alt.Tooltip("temp_max:Q", title="Max (°C)", format=".1f"),
        ],
    )
    line_min = alt.Chart(daily).mark_line(color="#60A5FA", strokeDash=[4, 2]).encode(
        x=alt.X("date:T", axis=date_axis),
        y=alt.Y("temp_min:Q"),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%a %d"),
            alt.Tooltip("temp_min:Q", title="Min (°C)", format=".1f"),
        ],
    )
    temp_chart = alt.layer(band, line_max, line_min).properties(height=300)
    st.subheader("🌡️ Temperature Forecast (°C)")
    st.altair_chart(temp_chart, use_container_width=True)

with col_right:
    precip_chart = (
        alt.Chart(daily)
        .mark_bar()
        .encode(
            x=alt.X("date:T", axis=date_axis),
            y=alt.Y("precipitation_sum:Q", title="mm", axis=y_axis),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%a %d"),
                alt.Tooltip("precipitation_sum:Q", title="Precipitation (mm)", format=".1f"),
            ],
        )
        .properties(height=300)
    )
    st.subheader("🌧️ Precipitation Forecast (mm)")
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