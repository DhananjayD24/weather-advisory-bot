from app.services.llm_service import get_llm


RESPONSE_PROMPT = """
You are the response-writing component of a weather-advisory support bot.

Your job is ONLY to turn the provided structured facts into a clear,
concise response for the user.

STRICT RULES:
- The selected SOP is authoritative.
- Never change the SOP's severity.
- Never change the SOP's action.
- Never invent safety advice.
- Never add advice that is not supported by the provided SOP guidance.
- Use the provided weather values exactly.
- If no SOP is provided, clearly say that no applicable SOP covers the scenario.
- If weather data is unavailable, do not guess the weather.
- Mention the SOP name or ID so the answer remains traceable.
- Do not claim that the advice comes from an official authority.
- Keep the response concise and natural.

STRUCTURED FACTS:
"""


def generate_llm_response(state: dict) -> str:
    """
    Convert an already-determined SOP decision into a natural response.

    Gemini does not make the safety decision.
    """

    error = state.get("error")

    if error:
        return (
            f"I could not provide weather-based guidance because "
            f"{error}"
        )

    selected_sop = state.get("selected_sop")
    decision = state.get("decision")
    weather = state.get("weather", {})
    activity = state.get("activity")
    location = state.get("location")
    time_context = state.get("time_context")

    if not selected_sop or not decision:
        return (
            "No applicable SOP covers this scenario, so I cannot "
            "provide safety guidance."
        )

    current = weather.get("current", {})

    prompt = RESPONSE_PROMPT + f"""
User activity: {activity}
Location: {location}
Requested time: {time_context}

Weather:
- Temperature: {current.get("temperature_2m")}
- Apparent temperature: {current.get("apparent_temperature")}
- Precipitation: {current.get("precipitation")}
- Rain: {current.get("rain")}
- Wind speed: {current.get("wind_speed_10m")}
- Wind gusts: {current.get("wind_gusts_10m")}
- Weather code: {current.get("weather_code")}

Selected SOP:
- ID: {selected_sop.get("id")}
- Name: {selected_sop.get("name")}

Decision:
- Severity: {decision.get("severity")}
- Action: {decision.get("action")}
- Guidance: {decision.get("guidance")}

Write the final response now.
"""

    llm = get_llm()

    response = llm.invoke(prompt)

    content = response.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)

            elif isinstance(block, dict):
                text = block.get("text")

                if text:
                    parts.append(text)

        result = "".join(parts).strip()

        if result:
            return result

    raise ValueError("Gemini returned an unexpected response format.")