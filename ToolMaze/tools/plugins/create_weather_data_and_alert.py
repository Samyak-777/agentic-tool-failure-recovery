"""
create_weather_data_and_alert Tool Plugin

Function: Fetch weather, build a structured payload, and notify the user
Category: Action
Domain: Travel
"""

TOOL_NAME = "create_weather_data_and_alert"

from tools.plugins import build_weather_data_payload as bwdp
from tools.plugins import create_document_and_alert_from_data as cdaafd
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

    result = cdaafd.execute(
        {
            "data": payload.get("data"),
            "title": payload.get("title"),
            "tags": payload.get("tags"),
            "user_id": payload.get("user_id"),
            "priority": payload.get("priority"),
            "channel": payload.get("channel"),
        },
        context,
    )
    if "error" in result:
        return result

    result["city"] = city
    result["workflow"] = "weather_structured_brief"
    return result
