import streamlit as st
from fetch import fetch_weather, geocode_city
from storage import save_weather, load_hourly, load_daily

st.set_page_config(page_title="Weather Dashboard", layout="wide")

with st.sidebar:
    st.header("Location")
    city = st.text_input("City name", value="Berlin")
    if st.button("Fetch & Refresh Data"):
        with st.spinner("Looking up city..."):
            try:
                lat, lon, label = geocode_city(city)
                st.caption(f"Found: {label} ({lat:.4f}, {lon:.4f})")
            except ValueError as e:
                st.error(str(e))
                st.stop()
        with st.spinner("Fetching weather..."):
            data = fetch_weather(lat, lon)
            save_weather(data)
        st.success(f"Data updated for {label}.")

st.title(f"7-Day Weather Forecast — {city}")

daily = load_daily()
hourly = load_hourly()

if daily.empty:
    st.info("No data yet. Use the sidebar to fetch weather data.")
    st.stop()

today = daily.iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Max Temp Today", f"{today['temp_max']:.1f} °C")
col2.metric("Min Temp Today", f"{today['temp_min']:.1f} °C")
col3.metric("Precipitation Today", f"{today['precipitation_sum']:.1f} mm")
col4.metric("Days of forecast", len(daily))

daily_chart = daily.set_index("date")[["temp_max", "temp_min"]].rename(
    columns={"temp_max": "Max °C", "temp_min": "Min °C"}
)
st.subheader("Daily Temperature Forecast (°C)")
st.line_chart(daily_chart)

st.subheader("Daily Precipitation Forecast (mm)")
st.bar_chart(daily.set_index("date")["precipitation_sum"].rename("Precip mm"))

st.subheader("Daily Summary")
st.dataframe(daily.rename(columns={
    "date": "Date",
    "temp_max": "Max °C",
    "temp_min": "Min °C",
    "precipitation_sum": "Precip mm",
}), use_container_width=True)