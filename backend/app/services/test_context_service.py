from app.services.context_service import merge_query_context
from app.services.query_parser import ParsedQuery


def test_context_is_retained_when_new_query_has_no_location():
    state = {
        "activity": "cycling",
        "location": "Bhopal",
        "time_context": "today",
        "user_type": None,
        "latitude": 23.2599,
        "longitude": 77.4126,
        "weather": {"current": {"temperature_2m": 25}},
        "matched_sops": [{"id": "EXERCISE_FAVORABLE_WEATHER"}],
        "selected_sop": {"id": "EXERCISE_FAVORABLE_WEATHER"},
        "decision": {"severity": "low"},
    }

    parsed = ParsedQuery(
        activity=None,
        location=None,
        time_context="this evening",
        user_type=None,
    )

    result = merge_query_context(state, parsed)

    assert result["location"] == "Bhopal"
    assert result["activity"] == "cycling"
    assert result["time_context"] == "this evening"

    # Weather decision must be refreshed because time changed.
    assert result["weather"] is None
    assert result["matched_sops"] == []
    assert result["selected_sop"] is None
    assert result["decision"] is None

    # Location did not change, so coordinates are retained.
    assert result["latitude"] == 23.2599
    assert result["longitude"] == 77.4126


def test_coordinates_are_cleared_when_location_changes():
    state = {
        "activity": "cycling",
        "location": "Bhopal",
        "time_context": "today",
        "user_type": None,
        "latitude": 23.2599,
        "longitude": 77.4126,
        "weather": {"current": {"temperature_2m": 25}},
        "matched_sops": [],
        "selected_sop": None,
        "decision": None,
    }

    parsed = ParsedQuery(
        activity=None,
        location="Pune",
        time_context=None,
        user_type=None,
    )

    result = merge_query_context(state, parsed)

    assert result["location"] == "Pune"

    # Old Bhopal coordinates must not be reused.
    assert result["latitude"] is None
    assert result["longitude"] is None

    assert result["weather"] is None
    assert result["matched_sops"] == []


def test_activity_change_refreshes_sop_decision():
    state = {
        "activity": "cycling",
        "location": "Bhopal",
        "time_context": "today",
        "user_type": None,
        "latitude": 23.2599,
        "longitude": 77.4126,
        "weather": {"current": {"temperature_2m": 25}},
        "matched_sops": [{"id": "EXERCISE_FAVORABLE_WEATHER"}],
        "selected_sop": {"id": "EXERCISE_FAVORABLE_WEATHER"},
        "decision": {"severity": "low"},
    }

    parsed = ParsedQuery(
        activity="running",
        location=None,
        time_context=None,
        user_type=None,
    )

    result = merge_query_context(state, parsed)

    assert result["activity"] == "running"
    assert result["location"] == "Bhopal"

    assert result["weather"] is None
    assert result["matched_sops"] == []
    assert result["selected_sop"] is None
    assert result["decision"] is None