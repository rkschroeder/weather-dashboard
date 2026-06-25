def parse_weather(data: dict) -> tuple[list[tuple], list[tuple]]:
    """Parse raw API response into (hourly_rows, daily_rows) ready for DB upsert."""
    try:
        hourly_rows = list(zip(
            data["hourly"]["time"],
            data["hourly"]["temperature_2m"],
            data["hourly"]["precipitation"],
            data["hourly"]["windspeed_10m"],
            data["hourly"]["winddirection_10m"],
            data["hourly"]["relativehumidity_2m"],
            data["hourly"]["uv_index"],
            data["hourly"]["cloudcover"],
        ))
        daily_rows = list(zip(
            data["daily"]["time"],
            data["daily"]["temperature_2m_max"],
            data["daily"]["temperature_2m_min"],
            data["daily"]["precipitation_sum"],
            data["daily"]["windspeed_10m_max"],
            data["daily"]["winddirection_10m_dominant"],
            data["daily"]["sunrise"],
            data["daily"]["sunset"],
        ))
    except KeyError as e:
        raise ValueError(f"Unexpected weather data structure: missing field {e}") from e

    return hourly_rows, daily_rows