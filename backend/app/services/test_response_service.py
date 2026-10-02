from app.services.response_service import build_response


def test_sop_response_is_traceable():
    state = {
        "selected_sop": {
            "id": "EXERCISE_HIGH_WIND",
            "name": "High wind during outdoor exercise",
        },
        "decision": {
            "severity": "high",
            "action": "avoid",
            "guidance": "Avoid strenuous outdoor exercise because strong wind gusts can make outdoor activity unsafe.",
        },
        "weather": {
            "current": {
                "temperature_2m": 25,
                "apparent_temperature": 26,
                "precipitation": 0,
                "wind_speed_10m": 30,
                "wind_gusts_10m": 45,
            }
        },
    }

    response = build_response(state)

    assert "EXERCISE_HIGH_WIND" in response
    assert "high" in response
    assert "avoid" in response
    assert "45" in response


def test_no_sop_does_not_give_advice():
    state = {
        "selected_sop": None,
        "decision": None,
        "weather": {
            "current": {
                "temperature_2m": 25,
            }
        },
    }

    response = build_response(state)

    assert "No applicable SOP" in response
    assert "cannot provide safety guidance" in response


def test_weather_error_is_honest():
    state = {
        "error": "Weather service is unavailable.",
        "selected_sop": None,
        "decision": None,
    }

    response = build_response(state)

    assert "Weather service is unavailable." in response