from datetime import datetime
from typing import Any


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _get_hourly_indexes(
    weather: dict[str, Any],
    time_context: str | None,
) -> list[int]:
    """
    Determine which hourly forecast entries are relevant
    to the user's requested time.
    """

    hourly = weather.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        return []

    parsed_times = [_parse_datetime(time) for time in times]

    current_time_raw = weather.get("current", {}).get("time")

    if not current_time_raw:
        return [0]

    current_time = _parse_datetime(current_time_raw)
    current_date = current_time.date()

    context = (time_context or "now").lower()

    # Current / now
    if context in {"now", "currently", "right now"}:
        future_indexes = [
            i
            for i, time in enumerate(parsed_times)
            if time >= current_time
        ]

        return future_indexes[:1] or [0]

    # Today
    if context in {"today", "this day"}:
        indexes = [
            i
            for i, time in enumerate(parsed_times)
            if time.date() == current_date
            and time >= current_time
        ]

        return indexes or [
            i
            for i, time in enumerate(parsed_times)
            if time.date() == current_date
        ]

    # This evening / tonight
    if context in {
        "this evening",
        "evening",
        "tonight",
        "today evening",
    }:
        indexes = [
            i
            for i, time in enumerate(parsed_times)
            if time.date() == current_date
            and 17 <= time.hour <= 22
        ]

        return indexes

    # Tomorrow
    if context in {"tomorrow", "next day"}:
        tomorrow = current_date.fromordinal(
            current_date.toordinal() + 1
        )

        return [
            i
            for i, time in enumerate(parsed_times)
            if time.date() == tomorrow
        ]

    # Tomorrow morning
    if context in {
        "tomorrow morning",
        "tomorrow early morning",
    }:
        tomorrow = current_date.fromordinal(
            current_date.toordinal() + 1
        )

        return [
            i
            for i, time in enumerate(parsed_times)
            if time.date() == tomorrow
            and 5 <= time.hour <= 11
        ]

    # Tomorrow afternoon
    if context in {
        "tomorrow afternoon",
    }:
        tomorrow = current_date.fromordinal(
            current_date.toordinal() + 1
        )

        return [
            i
            for i, time in enumerate(parsed_times)
            if time.date() == tomorrow
            and 12 <= time.hour <= 16
        ]

    # Tomorrow evening
    if context in {
        "tomorrow evening",
        "tomorrow night",
    }:
        tomorrow = current_date.fromordinal(
            current_date.toordinal() + 1
        )

        return [
            i
            for i, time in enumerate(parsed_times)
            if time.date() == tomorrow
            and 17 <= time.hour <= 22
        ]

    # Unknown time expression:
    # use the next available hourly forecast.
    future_indexes = [
        i
        for i, time in enumerate(parsed_times)
        if time >= current_time
    ]

    return future_indexes[:1] or [0]


def _aggregate_hourly_weather(
    weather: dict[str, Any],
    indexes: list[int],
) -> dict[str, Any]:
    """
    Convert the selected hourly forecast period into a weather
    snapshot that the SOP engine can evaluate.

    For safety thresholds we use conservative aggregation:
    - maximum temperature
    - maximum apparent temperature
    - maximum precipitation
    - maximum rain
    - maximum wind
    - maximum wind gust
    - maximum snowfall
    - highest precipitation probability
    - any severe weather code
    """

    hourly = weather.get("hourly", {})

    if not indexes:
        return {}

    def values(field: str) -> list[Any]:
        source = hourly.get(field, [])

        return [
            source[index]
            for index in indexes
            if index < len(source) and source[index] is not None
        ]

    def maximum(field: str, default: float = 0.0) -> float:
        field_values = values(field)

        if not field_values:
            return default

        return max(field_values)

    weather_codes = values("weather_code")

    return {
        "temperature_2m": maximum("temperature_2m"),
        "apparent_temperature": maximum("apparent_temperature"),
        "precipitation_probability": maximum(
            "precipitation_probability"
        ),
        "precipitation": maximum("precipitation"),
        "rain": maximum("rain"),
        "showers": maximum("showers"),
        "snowfall": maximum("snowfall"),
        "weather_code": (
            max(weather_codes)
            if weather_codes
            else None
        ),
        "wind_speed_10m": maximum("wind_speed_10m"),
        "wind_gusts_10m": maximum("wind_gusts_10m"),
    }


def select_weather_context(
    weather: dict[str, Any],
    time_context: str | None,
) -> dict[str, Any]:
    """
    Select the weather relevant to the user's requested time.

    The returned structure intentionally preserves the same
    `current` shape expected by the SOP engine.
    """

    indexes = _get_hourly_indexes(
        weather,
        time_context,
    )

    if not indexes:
        return weather

    selected = _aggregate_hourly_weather(
        weather,
        indexes,
    )

    if not selected:
        return weather

    return {
        **weather,
        "current": selected,
        "selected_time_context": time_context,
        "selected_hour_indexes": indexes,
    }