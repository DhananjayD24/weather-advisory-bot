from typing import Any


def build_weather_summary(weather: dict[str, Any]) -> str:
    current = weather.get("current", {})

    temperature = current.get("temperature_2m")
    apparent_temperature = current.get("apparent_temperature")
    precipitation = current.get("precipitation")
    wind_speed = current.get("wind_speed_10m")
    wind_gusts = current.get("wind_gusts_10m")
    units_key = "hourly_units" if "selected_hour_indexes" in weather else "current_units"
    units = weather.get(units_key, {})

    facts = []

    if temperature is not None:
        facts.append(f"temperature {temperature}{units.get('temperature_2m', '')}")

    if apparent_temperature is not None:
        facts.append(f"feels-like {apparent_temperature}{units.get('apparent_temperature', '')}")

    if precipitation is not None:
        facts.append(f"precipitation {precipitation}{units.get('precipitation', '')}")

    if wind_speed is not None:
        facts.append(f"wind {wind_speed}{units.get('wind_speed_10m', '')}")

    if wind_gusts is not None:
        facts.append(f"gusts {wind_gusts}{units.get('wind_gusts_10m', '')}")

    if not facts:
        return "Live weather data was retrieved, but the relevant weather values were unavailable."

    return ", ".join(facts)


def build_sop_response(
    state: dict[str, Any],
) -> str:
    """
    Build a response entirely from the selected SOP and live weather facts.
    No model-generated safety decision is made here.
    """

    selected_sop = state.get("selected_sop")
    decision = state.get("decision")
    weather = state.get("weather")

    if not selected_sop or not decision:
        return (
            "No applicable SOP was found for this request. "
            "I cannot provide safety guidance for this scenario."
        )

    severity = decision.get("severity", "unknown")
    action = decision.get("action", "unknown")
    guidance = decision.get("guidance", "")

    weather_summary = build_weather_summary(weather or {})

    sop_id = selected_sop.get("id", "unknown")
    sop_name = selected_sop.get("name", "Unnamed SOP")

    return (
        f"SOP: {sop_name} ({sop_id})\n"
        f"Severity: {severity}\n"
        f"Action: {action}\n"
        f"Weather for requested period: {weather_summary}\n"
        f"Guidance: {guidance}"
    )


def build_error_response(state: dict[str, Any]) -> str:
    error = state.get("error")

    if not error:
        return "I could not provide guidance for this request."

    return (
        f"I could not evaluate which SOP applies because {error}. "
        "I will not guess weather conditions or provide unsupported guidance."
    )


def build_response(state: dict[str, Any]) -> str:
    """
    Build the deterministic response for the current graph state.
    """

    if state.get("error"):
        return build_error_response(state)

    if not state.get("selected_sop"):
        return (
            "No applicable SOP was found for this scenario. "
            "I cannot provide safety guidance without an applicable SOP."
        )

    return build_sop_response(state)