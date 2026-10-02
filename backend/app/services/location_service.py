import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class LocationError(Exception):
    """Raised when a location cannot be resolved."""
    pass


async def resolve_location(location: str) -> dict:
    """
    Resolve a city/location name using Open-Meteo geocoding.
    """

    if not location:
        raise LocationError("Location was not provided.")

    params = {
        "name": location,
        "count": 5,
        "language": "en",
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                GEOCODING_URL,
                params=params,
            )

            response.raise_for_status()

    except httpx.TimeoutException as exc:
        raise LocationError(
            "Location service timed out."
        ) from exc

    except httpx.HTTPError as exc:
        raise LocationError(
            "Location service is unavailable."
        ) from exc

    data = response.json()

    results = data.get("results", [])

    if not results:
        raise LocationError(
            f"Could not find the location '{location}'."
        )

    result = results[0]

    return {
        "name": result.get("name"),
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "country": result.get("country"),
        "country_code": result.get("country_code"),
        "admin1": result.get("admin1"),
    }