from app.graph.state import WeatherState
from app.services.query_parser import ParsedQuery


def merge_query_context(
    state: WeatherState,
    parsed: ParsedQuery,
) -> WeatherState:
    """
    Merge information from the current user message with
    information retained from previous turns.
    """

    old_activity = state.get("activity")
    old_location = state.get("location")
    old_time = state.get("time_context")
    old_user_type = state.get("user_type")

    new_activity = parsed.activity or old_activity
    new_location = parsed.location or old_location
    new_time = parsed.time_context or old_time
    new_user_type = parsed.user_type or old_user_type

    location_changed = new_location != old_location

    context_changed = (
        new_activity != old_activity
        or new_location != old_location
        or new_time != old_time
        or new_user_type != old_user_type
    )

    updated_state = {
        **state,
        "activity": new_activity,
        "location": new_location,
        "time_context": new_time,
        "user_type": new_user_type,
    }

    if context_changed:
        updated_state["weather"] = None
        updated_state["matched_sops"] = []
        updated_state["selected_sop"] = None
        updated_state["decision"] = None

    # Coordinates belong specifically to the resolved location.
    # They must be discarded when the location changes.
    if location_changed:
        updated_state["latitude"] = None
        updated_state["longitude"] = None

    return updated_state