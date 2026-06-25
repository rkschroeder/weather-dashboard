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

now = pd.Timestamp.now()
current_humidity = None
if not hourly.empty and "humidity" in hourly.columns:
    closest = (hourly["time"] - now).abs().idxmin()
    current_humidity = hourly.loc[closest, "humidity"]

st.subheader("Today at a Glance")
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("🌡️ Max Temp (°C)", f"{today['temp_max']:.1f}")
col2.metric("❄️ Min Temp (°C)", f"{today['temp_min']:.1f}")
col3.metric("🌧️ Precipitation (mm)", f"{today['precipitation_sum']:.1f}")
col4.metric("💨 Wind Speed (km/h)", f"{today['wind_speed_max']:.1f}" if today["wind_speed_max"] is not None else "—")
col5.metric("🧭 Wind Direction", degrees_to_compass(today["wind_direction_dominant"]) if today["wind_direction_dominant"] is not None else "—")
col6.metric("💧 Humidity (%)", f"{current_humidity:.0f}" if current_humidity is not None else "—")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2, gap="large")

date_axis = alt.Axis(format="%a %d", tickCount="day", labelAngle=-30, title=None)

with col_left:
    temp_data = daily[["date", "temp_max", "temp_min"]].melt(
        "date", var_name="series", value_name="°C"
    )
    temp_data["series"] = temp_data["series"].map({"temp_max": "Max", "temp_min": "Min"})
    temp_chart = (
        alt.Chart(temp_data)
        .mark_line()
        .encode(
            x=alt.X("date:T", axis=date_axis),
            y=alt.Y("°C:Q", title="°C"),
            color=alt.Color("series:N", legend=alt.Legend(orient="none", legendX=8, legendY=5, title=None)),
        )
        .properties(height=300)
    )
    st.subheader("🌡️ Temperature Forecast (°C)")
    st.altair_chart(temp_chart, use_container_width=True)

with col_right:
    precip_chart = (
        alt.Chart(daily)
        .mark_bar()
        .encode(
            x=alt.X("date:T", axis=date_axis),
            y=alt.Y("precipitation_sum:Q", title="mm"),
        )
        .properties(height=300)
    )
    st.subheader("🌧️ Precipitation Forecast (mm)")
    st.altair_chart(precip_chart, use_container_width=True)

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
        y=alt.Y("wind_speed:Q", title="km/h"),
    )
    .properties(height=300)
)
st.subheader("💨 Wind Speed Forecast (km/h)")
st.altair_chart(wind_chart, use_container_width=True)

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
            y=alt.Y("humidity:Q", title="%", scale=alt.Scale(domain=[0, 100])),
        )
        .properties(height=300)
    )
    st.subheader("💧 Humidity Forecast (%)")
    st.altair_chart(humidity_chart, use_container_width=True)

st.divider()

# ── Summary table ─────────────────────────────────────────────────────────────
st.subheader("📋 Daily Summary")
summary = daily.copy()
summary["wind_compass"] = summary["wind_direction_dominant"].apply(
    lambda d: degrees_to_compass(d) if d is not None else "—"
)
summary["date"] = summary["date"].dt.strftime("%a %d")
st.dataframe(
    summary.drop(columns=["wind_direction_dominant"]).rename(columns={
        "date": "Date",
        "temp_max": "Max Temp (°C)",
        "temp_min": "Min Temp (°C)",
        "precipitation_sum": "Precipitation (mm)",
        "wind_speed_max": "Wind Speed (km/h)",
        "wind_compass": "Wind Dir",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("""
<div class="footer">
    Data from <a href="https://open-meteo.com/" style="color: rgba(255,255,255,0.4);">Open-Meteo</a>
    · Free & open-source weather API
</div>
""", unsafe_allow_html=True)