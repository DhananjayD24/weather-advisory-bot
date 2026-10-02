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
            return False

        return compare(actual_value, operator, threshold)

    # Weather-code condition
    if condition_type == "weather_condition":
        weather_code = current.get("weather_code")

        if weather_code is None:
            return False

        allowed_codes = condition.get("weather_codes", [])

        return weather_code in allowed_codes

    # Favorable-weather condition
    if condition_type == "favorable_weather":
        weather_code = current.get("weather_code")
        precipitation = current.get("precipitation")
        wind_gusts = current.get("wind_gusts_10m")
        apparent_temperature = current.get("apparent_temperature")

        if any(
            value is None
            for value in [
                weather_code,
                precipitation,
                wind_gusts,
                apparent_temperature,
            ]
        ):
            return False

        return (
            weather_code in [0, 1, 2]
            and precipitation == 0
            and wind_gusts < 30
            and apparent_temperature < 35
        )

    return False

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