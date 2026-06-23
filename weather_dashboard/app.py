import streamlit as st
from fetch import fetch_weather, geocode_city, FetchError
from storage import save_weather, load_hourly, load_daily
from utils import degrees_to_compass

st.set_page_config(page_title="Weather Dashboard", layout="wide")

with st.sidebar:
    st.header("Location")
    city = st.text_input("City name", value="Berlin")

    # Clear cached results whenever the city input changes
    if st.session_state.get("_prev_city") != city:
        st.session_state.pop("geo_results", None)
        st.session_state["_prev_city"] = city

    if st.button("Search City"):
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
            st.caption(f"Found: {selected['label']} ({selected['lat']:.4f}, {selected['lon']:.4f})")
        else:
            labels = [r["label"] for r in results]
            choice = st.radio(f"{len(results)} matches found — select one:", labels)
            selected = results[labels.index(choice)]

        if st.button("Fetch Weather"):
            with st.spinner("Fetching weather..."):
                try:
                    data = fetch_weather(selected["lat"], selected["lon"])
                    save_weather(data)
                except (ValueError, FetchError) as e:
                    st.error(str(e))
                    st.stop()
            st.success(f"Data updated for {selected['label']}.")

st.title(f"7-Day Weather Forecast — {city}")

daily = load_daily()
hourly = load_hourly()

if daily.empty:
    st.info("No data yet. Use the sidebar to fetch weather data.")
    st.stop()

today = daily.iloc[0]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Max Temp Today", f"{today['temp_max']:.1f} °C")
col2.metric("Min Temp Today", f"{today['temp_min']:.1f} °C")
col3.metric("Precipitation Today", f"{today['precipitation_sum']:.1f} mm")
col4.metric("Max Wind Today", f"{today['wind_speed_max']:.1f} km/h" if today['wind_speed_max'] is not None else "—")
col5.metric("Wind Direction Today", degrees_to_compass(today['wind_direction_dominant']) if today['wind_direction_dominant'] is not None else "—")

daily_chart = daily.set_index("date")[["temp_max", "temp_min"]].rename(
    columns={"temp_max": "Max °C", "temp_min": "Min °C"}
)
st.subheader("Daily Temperature Forecast (°C)")
st.line_chart(daily_chart)

st.subheader("Daily Precipitation Forecast (mm)")
st.bar_chart(daily.set_index("date")["precipitation_sum"].rename("Precip mm"))

st.subheader("Daily Wind Forecast")
st.line_chart(daily.set_index("date")["wind_speed_max"].rename("Max Wind km/h"))

st.subheader("Daily Summary")
summary = daily.copy()
summary["wind_compass"] = summary["wind_direction_dominant"].apply(
    lambda d: degrees_to_compass(d) if d is not None else "—"
)
st.dataframe(summary.rename(columns={
    "date": "Date",
    "temp_max": "Max °C",
    "temp_min": "Min °C",
    "precipitation_sum": "Precip mm",
    "wind_speed_max": "Max Wind km/h",
    "wind_direction_dominant": "Wind Dir °",
    "wind_compass": "Wind Dir",
}), use_container_width=True)