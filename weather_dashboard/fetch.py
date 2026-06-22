import requests

BASE_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

DEFAULT_PARAMS = {
    "latitude": 52.52,
    "longitude": 13.41,
    "hourly": "temperature_2m,precipitation,windspeed_10m,winddirection_10m",
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,winddirection_10m_dominant",
    "timezone": "auto",
    "forecast_days": 7,
}


def geocode_city(city: str) -> tuple[float, float, str]:
    response = requests.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "en"}, timeout=10)
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        raise ValueError(f"City not found: {city!r}")
    r = results[0]
    return r["latitude"], r["longitude"], f"{r['name']}, {r.get('country', '')}"


def fetch_weather(latitude: float = 52.52, longitude: float = 13.41) -> dict:
    params = {**DEFAULT_PARAMS, "latitude": latitude, "longitude": longitude}
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()