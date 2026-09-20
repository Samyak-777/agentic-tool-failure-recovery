"""
build_weather_text_report Tool Plugin

Function: Build a text-based travel weather briefing payload
Category: Processor
Domain: Travel
"""

TOOL_NAME = "build_weather_text_report"


def execute(arguments, context) -> dict:
    del context

    weather_data = arguments.get("weather_data")
    converted_data = arguments.get("converted_data")
    city = arguments.get("city")

    if not isinstance(weather_data, dict):
        return {"error": "weather_data must be an object"}
    if not isinstance(converted_data, dict):
        return {"error": "converted_data must be an object"}
    if not city:
        return {"error": "city is required"}

    content = "\n".join([
        f"City: {city}",
        f"Condition: {weather_data.get('condition')}",
        f"Temperature (C): {weather_data.get('temperature_celsius')}",
        f"Temperature ({converted_data.get('to_unit', 'fahrenheit')[0].upper()}): {converted_data.get('converted_value')}",
    ])

    return {
        "title": arguments.get("title") or "Travel Weather Brief",
        "content": content,
        "tags": ["weather", str(city).lower().replace(" ", "_")],
        "user_id": arguments.get("user_id") or "default_user",
        "priority": arguments.get("priority") or "medium",
        "channel": arguments.get("channel") or "app",
    }
