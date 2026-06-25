import logging
import requests

BASE_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

_FORECAST_PARAMS = {
    "hourly": "temperature_2m,precipitation,windspeed_10m,winddirection_10m,relativehumidity_2m,uv_index,cloudcover",
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,winddirection_10m_dominant,sunrise,sunset",
    "timezone": "auto",
    "forecast_days": 7,
}

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Raised when an API request or response parsing fails."""


_MAX_GEOCODE_RESULTS = 15


def geocode_city(city: str) -> list[dict]:
    """Return up to 15 matching locations as dicts with keys: lat, lon, label."""
    logger.debug("Geocoding city: %r", city)
    try:
        response = requests.get(GEOCODING_URL, params={"name": city, "count": 50, "language": "en"}, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Geocoding request failed for %r: %s", city, e)
        raise FetchError(str(e)) from e

    results = response.json().get("results")
    if not results:
        raise ValueError(f"City not found: {city!r}")

    city_lower = city.strip().lower()
    locations = []
    for r in results:
        try:
            name = r["name"]
            # Skip results whose city name doesn't contain the search term
            # (the API can return fuzzy/alias matches unrelated to the query)
            if city_lower not in name.lower():
                continue
            parts = [name]
            if r.get("admin1"):
                parts.append(r["admin1"])
            parts.append(r.get("country", ""))
            label = ", ".join(p for p in parts if p)
            locations.append({"lat": r["latitude"], "lon": r["longitude"], "label": label})
        except KeyError as e:
            logger.warning("Skipping geocoding result with missing field %s: %r", e, r)
        if len(locations) == _MAX_GEOCODE_RESULTS:
            break

    if not locations:
        raise ValueError(f"City not found: {city!r}")

    logger.debug("Geocoded %r → %d result(s)", city, len(locations))
    return locations


def fetch_weather(latitude: float, longitude: float) -> dict:
    logger.debug("Fetching weather for lat=%s, lon=%s", latitude, longitude)
    params = {**_FORECAST_PARAMS, "latitude": latitude, "longitude": longitude}
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Weather fetch failed for lat=%s, lon=%s: %s", latitude, longitude, e)
        raise FetchError(str(e)) from e

    data = response.json()

    if not data.get("hourly") or not data.get("daily"):
        raise ValueError("Incomplete weather data in API response: missing hourly or daily fields")

    logger.debug(
        "Received weather data: %d hourly entries, %d daily entries",
        len(data["hourly"].get("time", [])),
        len(data["daily"].get("time", [])),
    )
    return data