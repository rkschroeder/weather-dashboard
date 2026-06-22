import logging
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

logger = logging.getLogger(__name__)


def geocode_city(city: str) -> tuple[float, float, str]:
    logger.debug("Geocoding city: %r", city)
    try:
        response = requests.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "en"}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Geocoding request failed for %r: %s", city, e)
        raise

    results = response.json().get("results")
    if not results:
        raise ValueError(f"City not found: {city!r}")

    try:
        r = results[0]
        lat, lon, label = r["latitude"], r["longitude"], f"{r['name']}, {r.get('country', '')}"
    except KeyError as e:
        raise ValueError(f"Unexpected geocoding response structure: missing field {e}") from e

    logger.debug("Geocoded %r → %s (%s, %s)", city, label, lat, lon)
    return lat, lon, label


def fetch_weather(latitude: float = 52.52, longitude: float = 13.41) -> dict:
    logger.debug("Fetching weather for lat=%s, lon=%s", latitude, longitude)
    params = {**DEFAULT_PARAMS, "latitude": latitude, "longitude": longitude}
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Weather fetch failed for lat=%s, lon=%s: %s", latitude, longitude, e)
        raise

    data = response.json()

    # Validate top-level structure before returning so callers get a clear error
    # rather than a KeyError deep inside save_weather().
    if not data.get("hourly") or not data.get("daily"):
        raise ValueError(f"Incomplete weather data in API response: missing hourly or daily fields")

    logger.debug(
        "Received weather data: %d hourly entries, %d daily entries",
        len(data["hourly"].get("time", [])),
        len(data["daily"].get("time", [])),
    )
    return data