import json
from pathlib import Path
from typing import Any


SOP_FILE = Path(__file__).resolve().parent.parent / "policies" / "sops.json"


def load_sops() -> list[dict[str, Any]]:
    """Load all SOP rules from the external JSON file."""

    with open(SOP_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def compare(value: float, operator: str, threshold: float) -> bool:
    """Evaluate a numeric comparison."""

    if operator == ">":
        return value > threshold

    if operator == ">=":
        return value >= threshold

    if operator == "<":
        return value < threshold

    if operator == "<=":
        return value <= threshold

    if operator == "==":
        return value == threshold

    return False


class IncompleteWeatherData(Exception):
    pass


SEVERE_WEATHER_CODES = {95, 96, 99}


def get_weather_codes(weather: dict[str, Any]) -> list[int]:
    """
    Return all relevant weather codes from the selected weather period.
    """

    hourly = weather.get("hourly", {})
    codes = hourly.get("weather_code", [])
    selected_indexes = weather.get("selected_hour_indexes")

    if selected_indexes is not None:
        selected_codes = [
            codes[index]
            for index in selected_indexes
            if index < len(codes) and isinstance(codes[index], int)
        ]
        if selected_codes:
            return selected_codes

    current_code = weather.get("current", {}).get("weather_code")

    if isinstance(current_code, int):
        return [current_code]

    valid_codes = [
        code for code in codes
        if isinstance(code, int)
    ]

    if valid_codes:
        return valid_codes

    return []


def has_thunderstorm(weather: dict[str, Any]) -> bool:
    return any(
        code in SEVERE_WEATHER_CODES
        for code in get_weather_codes(weather)
    )
    
def evaluate_condition(
    condition: dict[str, Any],
    weather: dict[str, Any],
) -> bool:
    """Evaluate one SOP condition against weather data."""

    condition_type = condition.get("type")

    current = weather.get("current", {})

    # Numeric condition
    if condition_type == "numeric":
        field = condition.get("field")
        operator = condition.get("operator")
        threshold = condition.get("value")

        actual_value = current.get(field)

        if actual_value is None:
            raise IncompleteWeatherData(
                f"Weather data is missing the required field '{field}'."
            )

        return compare(actual_value, operator, threshold)

    # Weather-code condition
    if condition_type == "weather_condition":
        allowed_codes = condition.get("weather_codes", [])

        weather_codes = get_weather_codes(weather)
        if not weather_codes:
            raise IncompleteWeatherData(
                "Weather data is missing the required weather code."
            )

        return any(
            code in allowed_codes
            for code in weather_codes
        )

    # Favorable-weather condition
    if condition_type == "favorable_weather":
        weather_code = current.get("weather_code")
        precipitation = current.get("precipitation")
        wind_gusts = current.get("wind_gusts_10m")
        apparent_temperature = current.get("apparent_temperature")

        required_values = {
            "weather_code": weather_code,
            "precipitation": precipitation,
            "wind_gusts_10m": wind_gusts,
            "apparent_temperature": apparent_temperature,
        }
        missing = [name for name, value in required_values.items() if value is None]
        if missing:
            raise IncompleteWeatherData(
                f"Weather data is missing required field(s): {', '.join(missing)}."
            )

        return (
            weather_code in [0, 1, 2]
            and precipitation == 0
            and wind_gusts < 30
            and apparent_temperature < 35
        )

        # Fuzzy weather assessment
    if condition_type == "fuzzy_weather_assessment":
        current = weather.get("current", {})

        precipitation = current.get("precipitation")
        precipitation_probability = current.get(
            "precipitation_probability"
        )
        wind_gusts = current.get("wind_gusts_10m")
        apparent_temperature = current.get(
            "apparent_temperature"
        )

        weather_codes = get_weather_codes(weather)
        if not weather_codes:
            raise IncompleteWeatherData(
                "Weather data is missing the required weather code."
            )
        if any(code in SEVERE_WEATHER_CODES for code in weather_codes):
            return False

        required_values = {
            "precipitation": precipitation,
            "precipitation_probability": precipitation_probability,
            "wind_gusts_10m": wind_gusts,
            "apparent_temperature": apparent_temperature,
        }
        missing = [name for name, value in required_values.items() if value is None]
        if missing:
            raise IncompleteWeatherData(
                f"Weather data is missing required field(s): {', '.join(missing)}."
            )

        # A picnic is considered broadly suitable when
        # there is little/no precipitation, reasonable wind,
        # and a comfortable apparent temperature.
        return (
            precipitation == 0
            and precipitation_probability < 30
            and wind_gusts < 30
            and 15 <= apparent_temperature < 35
        )

def sop_applies_to_activity(
    sop: dict[str, Any],
    activity: str | None,
) -> bool:
    """Check whether an SOP is relevant to the requested activity."""

    if not activity:
        return False

    activity = activity.lower().strip()

    applicable_activities = [
        item.lower().strip()
        for item in sop.get("applies_to", [])
    ]

    return activity in applicable_activities


def required_weather_fields(activity: str | None) -> set[str]:
    """Return API fields needed by policies applicable to this activity."""
    fields: set[str] = set()

    for sop in load_sops():
        if not sop_applies_to_activity(sop, activity):
            continue

        condition = sop.get("conditions", {})
        condition_type = condition.get("type")

        if condition_type == "numeric" and condition.get("field"):
            fields.add(condition["field"])
        elif condition_type == "weather_condition":
            fields.add("weather_code")
        elif condition_type == "favorable_weather":
            fields.update({
                "weather_code",
                "precipitation",
                "wind_gusts_10m",
                "apparent_temperature",
            })
        elif condition_type == "fuzzy_weather_assessment":
            fields.update({
                "weather_code",
                "precipitation",
                "precipitation_probability",
                "wind_gusts_10m",
                "apparent_temperature",
            })

    return fields


def match_sops(
    weather: dict[str, Any],
    activity: str | None,
) -> list[dict[str, Any]]:
    """
    Return every SOP that applies to the activity
    and matches the current weather.
    """

    matched = []

    for sop in load_sops():

        if not sop_applies_to_activity(sop, activity):
            continue

        condition = sop.get("conditions", {})

        if evaluate_condition(condition, weather):
            matched.append(sop)

    return matched

SEVERITY_RANK = {
    "low": 1,
    "moderate": 2,
    "high": 3,
    "critical": 4,
}


def resolve_sop_matches(
    matched_sops: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Resolve multiple matching SOPs into one selected SOP.

    Higher severity wins.
    If severity is equal, higher priority wins.
    """

    if not matched_sops:
        return None

    selected_sop = max(
        matched_sops,
        key=lambda sop: (
            SEVERITY_RANK.get(
                sop.get("decision", {}).get("severity", "low"),
                0,
            ),
            sop.get("priority", 0),
        ),
    )

    return selected_sop