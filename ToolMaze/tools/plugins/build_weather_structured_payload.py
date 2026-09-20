"""
build_weather_structured_payload Tool Plugin

Function: Fetch weather and build a structured weather payload
Category: Processor
Domain: Travel
"""

TOOL_NAME = "build_weather_structured_payload"

from tools.plugins import build_weather_data_payload as bwdp
from tools.plugins import get_weather_openweather as gwo


def execute(arguments, context) -> dict:
    city = arguments.get("city")
    weather_data = gwo.execute({"city": city}, context)
    if "error" in weather_data:
        return weather_data

    payload = bwdp.execute(
        {
            "weather_data": weather_data,
            "city": city,
            "title": arguments.get("title") or "Travel Weather Brief",
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in payload:
        return payload

    payload["city"] = city
    return payload
