from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import WeatherState
from app.services.query_parser import parse_query_with_gemini
from app.services.context_service import merge_query_context

from app.services.location_service import resolve_location as resolve_location_service
from app.services.location_service import LocationError

from app.services.weather_service import (
    fetch_weather as fetch_weather_service,
    WeatherError,
)

from app.services.sop_service import (
    match_sops as find_matching_sops,
    resolve_sop_matches,
)

from app.services.response_service import build_response

from app.services.weather_context_service import select_weather_context

from app.services.response_llm_service import generate_llm_response


def parse_query(state: WeatherState) -> WeatherState:
    print("NODE: parse_query")

    query = state.get("current_query", "").strip()

    if not query:
        return {
            **state,
            "error": "No user query provided.",
        }

    try:
        parsed = parse_query_with_gemini(query)

        return merge_query_context(
            state,
            parsed,
        )

    except ValueError as exc:
        return {
            **state,
            "error": str(exc),
        }

    except Exception:
        return {
            **state,
            "error": "Unable to understand the user request.",
        }
        
def route_after_parse(state: WeatherState):
    if state.get("error"):
        return "parse_error"

    return "check_context"

def check_context(state: WeatherState) -> WeatherState:
    print("NODE: check_context")
    return state


def route_context(
    state: WeatherState,
) -> Literal["resolve_location", "fetch_weather"]:

    print("ROUTER: route_context")

    if (
        state.get("latitude") is not None
        and state.get("longitude") is not None
    ):
        return "fetch_weather"

    return "resolve_location"


async def resolve_location(state: WeatherState) -> WeatherState:
    print("NODE: resolve_location")

    location = state.get("location")

    if not location:
        return {
            **state,
            "error": "Location is required to check weather.",
        }

    try:
        result = await resolve_location_service(location)

        return {
            **state,
            "location": result["name"],
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "error": None,
        }

    except LocationError as exc:
        return {
            **state,
            "latitude": None,
            "longitude": None,
            "error": str(exc),
        }

    except Exception:
        return {
            **state,
            "latitude": None,
            "longitude": None,
            "error": "Unable to resolve the requested location.",
        }

def route_after_location(
    state: WeatherState,
):
    if state.get("error"):
        return "location_error"

    if state.get("latitude") is None or state.get("longitude") is None:
        return "location_error"

    return "fetch_weather"

async def fetch_weather(state: WeatherState) -> WeatherState:
    print("NODE: fetch_weather")

    latitude = state.get("latitude")
    longitude = state.get("longitude")

    if latitude is None or longitude is None:
        return {
            **state,
            "weather": None,
            "error": "Weather cannot be fetched because location coordinates are missing.",
        }

    try:
        weather = await fetch_weather_service(
            latitude,
            longitude,
        )

        return {
            **state,
            "weather": weather,
            "error": None,
        }

    except WeatherError as exc:
        return {
            **state,
            "weather": None,
            "error": str(exc),
        }

    except Exception:
        return {
            **state,
            "weather": None,
            "error": "Unable to retrieve live weather data.",
        }

def route_after_weather(state: WeatherState):
    if state.get("error"):
        return "weather_error"

    if not state.get("weather"):
        return "weather_error"

    return "match_sops"

def match_sops(state: WeatherState) -> WeatherState:
    weather = state.get("weather")
    activity = state.get("activity")
    time_context = state.get("time_context")

    if not weather:
        return {
            **state,
            "matched_sops": [],
            "error": "Weather data is unavailable.",
        }

    selected_weather = select_weather_context(
        weather=weather,
        time_context=time_context,
    )

    matched = find_matching_sops(
        weather=selected_weather,
        activity=activity,
    )

    return {
        **state,
        "weather": selected_weather,
        "matched_sops": matched,
    }


def check_sop_match(
    state: WeatherState,
) -> Literal["no_guidance", "resolve_policy"]:

    print("NODE: check_sop_match")

    if state.get("matched_sops"):
        return "resolve_policy"

    return "no_guidance"


def resolve_policy(state: WeatherState) -> WeatherState:
    matched_sops = state.get("matched_sops", [])

    selected = resolve_sop_matches(matched_sops)

    if selected is None:
        return {
            **state,
            "selected_sop": None,
            "decision": None,
        }

    return {
        **state,
        "selected_sop": selected,
        "decision": selected.get("decision"),
    }


def no_guidance(state: WeatherState) -> WeatherState:
    print("NODE: no_guidance")
    return state

def location_error(state: WeatherState) -> WeatherState:
    print("NODE: location_error")
    return state

def parse_error(state: WeatherState) -> WeatherState:
    print("NODE: parse_error")
    return state

def weather_error(state: WeatherState) -> WeatherState:
    print("NODE: weather_error")
    return state

def generate_response(state: WeatherState) -> WeatherState:
    print("NODE: generate_response")

    response = generate_llm_response(state)

    return {
        **state,
        "response": response,
    }


def build_graph():

    graph = StateGraph(WeatherState)

    # Nodes
    graph.add_node("parse_query", parse_query)
    graph.add_node("check_context", check_context)
    graph.add_node("resolve_location", resolve_location)
    graph.add_node("fetch_weather", fetch_weather)
    graph.add_node("match_sops", match_sops)
    graph.add_node("resolve_policy", resolve_policy)
    graph.add_node("no_guidance", no_guidance)
    graph.add_node("generate_response", generate_response)
    graph.add_node("location_error", location_error)
    graph.add_node("parse_error", parse_error)
    graph.add_node("weather_error", weather_error)

    # Start
    graph.add_edge(START, "parse_query")

    # Query → Context decision
    graph.add_conditional_edges(
        "parse_query",
        route_after_parse,
        {
            "check_context": "check_context",
            "parse_error": "parse_error",
        },
    )

    graph.add_conditional_edges(
        "check_context",
        route_context,
        {
            "resolve_location": "resolve_location",
            "fetch_weather": "fetch_weather",
        },
    )

    # Location → Weather
    graph.add_conditional_edges(
    "resolve_location",
    route_after_location,
    {
        "fetch_weather": "fetch_weather",
        "location_error": "location_error",
    },
)

    # Weather → SOP matching
    graph.add_conditional_edges(
        "fetch_weather",
        route_after_weather,
        {
            "match_sops": "match_sops",
            "weather_error": "weather_error",
        },
    )

    # SOP matching → decision
    graph.add_conditional_edges(
        "match_sops",
        check_sop_match,
        {
            "no_guidance": "no_guidance",
            "resolve_policy": "resolve_policy",
        },
    )

    # Both outcomes → response
    graph.add_edge("no_guidance", "generate_response")
    graph.add_edge("resolve_policy", "generate_response")
    
    graph.add_edge("location_error", "generate_response")
    
    graph.add_edge("parse_error", "generate_response")
    
    graph.add_edge("weather_error", "generate_response")
    
    # Response → END
    graph.add_edge("generate_response", END)

    checkpointer = MemorySaver()

    return graph.compile(
        checkpointer=checkpointer
    )


graph = build_graph()