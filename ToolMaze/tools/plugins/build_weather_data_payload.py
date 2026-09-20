"""
build_weather_data_payload Tool Plugin

Function: Build a structured travel weather briefing payload
Category: Processor
Domain: Travel
"""

TOOL_NAME = "build_weather_data_payload"


def execute(arguments, context) -> dict:
    del context

    weather_data = arguments.get("weather_data")
    city = arguments.get("city")

    if not isinstance(weather_data, dict):
        return {"error": "weather_data must be an object"}
    if not city:
        return {"error": "city is required"}

    return {
        "data": {
            "city": city,
            "condition": weather_data.get("condition"),
            "temperature_celsius": weather_data.get("temperature_celsius"),
        },
        "title": arguments.get("title") or "Travel Weather Brief",
        "tags": ["weather", str(city).lower().replace(" ", "_"), "structured"],
        "user_id": arguments.get("user_id") or "default_user",
        "priority": arguments.get("priority") or "medium",
        "channel": arguments.get("channel") or "app",
    }
