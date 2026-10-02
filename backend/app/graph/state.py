from typing import TypedDict, Optional, List, Dict, Any


class WeatherState(TypedDict, total=False):
    # Conversation
    messages: List[Dict[str, Any]]

    # Current user request
    current_query: str
    activity: Optional[str]
    location: Optional[str]
    time_context: Optional[str]
    user_type: Optional[str]

    # Location information
    latitude: Optional[float]
    longitude: Optional[float]

    # Live weather
    weather: Optional[Dict[str, Any]]

    # SOP processing
    matched_sops: List[Dict[str, Any]]
    selected_sop: Optional[Dict[str, Any]]

    # Final policy decision
    decision: Optional[Dict[str, Any]]

    # Error handling
    error: Optional[str]
    
    response: Optional[str]