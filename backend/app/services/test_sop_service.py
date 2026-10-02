from app.services.sop_service import load_sops, match_sops
from app.services.sop_service import resolve_sop_matches


def test_sops_load():
    sops = load_sops()

    assert len(sops) >= 10


def test_high_wind_matches_cycling():
    weather = {
        "current": {
            "wind_gusts_10m": 45,
            "precipitation": 0,
            "rain": 0,
            "apparent_temperature": 25,
            "weather_code": 0
        }
    }

    matched = match_sops(weather, "cycling")

    ids = [sop["id"] for sop in matched]

    assert "EXERCISE_HIGH_WIND" in ids


def test_normal_weather_matches_favorable_exercise():
    weather = {
        "current": {
            "wind_gusts_10m": 5,
            "precipitation": 0,
            "rain": 0,
            "apparent_temperature": 24,
            "weather_code": 0
        }
    }

    matched = match_sops(weather, "cycling")

    ids = [sop["id"] for sop in matched]

    assert "EXERCISE_FAVORABLE_WEATHER" in ids
    
    
def test_highest_severity_wins():
    matched = [
        {
            "id": "RULE_LOW",
            "priority": 100,
            "decision": {
                "severity": "low"
            }
        },
        {
            "id": "RULE_HIGH",
            "priority": 10,
            "decision": {
                "severity": "high"
            }
        }
    ]

    selected = resolve_sop_matches(matched)

    assert selected["id"] == "RULE_HIGH"
    
def test_priority_breaks_severity_tie():
    matched = [
        {
            "id": "RULE_ONE",
            "priority": 20,
            "decision": {
                "severity": "high"
            }
        },
        {
            "id": "RULE_TWO",
            "priority": 80,
            "decision": {
                "severity": "high"
            }
        }
    ]

    selected = resolve_sop_matches(matched)

    assert selected["id"] == "RULE_TWO"
    
def test_no_matching_sop_returns_none():
    selected = resolve_sop_matches([])

    assert selected is None