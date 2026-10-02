import httpx


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherError(Exception):
    """Raised when live weather data cannot be retrieved."""
    pass


async def fetch_weather(
    latitude: float,
    longitude: float,
) -> dict:
    """
    Fetch live weather data from Open-Meteo.

    The requested fields are explicit so the downstream
    policy engine knows exactly which weather facts it has.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,

        # Current conditions
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
            "weather_code",
            "wind_speed_10m",
            "wind_gusts_10m",
        ]),

        # Hourly forecast
        "hourly": ",".join([
            "temperature_2m",
            "precipitation_probability",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
            "weather_code",
            "wind_speed_10m",
            "wind_gusts_10m",
        ]),

        # Enough forecast horizon for today/tomorrow queries
        "forecast_days": 2,

        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                FORECAST_URL,
                params=params,
            )

            response.raise_for_status()

    except httpx.TimeoutException as exc:
        raise WeatherError(
            "Weather service timed out."
        ) from exc

    except httpx.HTTPError as exc:
        raise WeatherError(
            "Weather service is unavailable."
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise WeatherError(
            "Weather service returned invalid data."
        ) from exc

    if not data.get("current") or not data.get("hourly"):
        raise WeatherError(
            "Weather service returned incomplete data."
        )

    return data