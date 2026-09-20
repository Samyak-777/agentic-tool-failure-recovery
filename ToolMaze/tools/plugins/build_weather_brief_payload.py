"""
build_weather_brief_payload Tool Plugin

Function: Fetch weather, convert temperature, and build a text weather brief payload
Category: Processor
Domain: Travel
"""

TOOL_NAME = "build_weather_brief_payload"

from tools.plugins import build_weather_text_report as bwtr
from tools.plugins import get_weather_openweather as gwo
from tools.plugins import temperature_converter as tc


def execute(arguments, context) -> dict:
    city = arguments.get("city")
    weather_data = gwo.execute({"city": city}, context)
    if "error" in weather_data:
        return weather_data

    converted_data = tc.execute(
        {
            "value": weather_data.get("temperature_celsius"),
            "from_unit": "celsius",
            "to_unit": arguments.get("to_unit") or "fahrenheit",
        },
        context,
    )
    if "error" in converted_data:
        return converted_data

    payload = bwtr.execute(
        {
            "weather_data": weather_data,
            "converted_data": converted_data,
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
    payload["converted_unit"] = converted_data.get("to_unit")
    return payload
