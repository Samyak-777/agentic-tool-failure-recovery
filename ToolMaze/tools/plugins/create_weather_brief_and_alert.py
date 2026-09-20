"""
create_weather_brief_and_alert Tool Plugin

Function: Fetch weather, convert temperature, build a text brief, and notify the user
Category: Action
Domain: Travel
"""

TOOL_NAME = "create_weather_brief_and_alert"

from tools.plugins import build_weather_text_report as bwtr
from tools.plugins import create_document_and_alert as cdaa
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

    report_payload = bwtr.execute(
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
    if "error" in report_payload:
        return report_payload

    result = cdaa.execute(
        {
            "content": report_payload.get("content"),
            "title": report_payload.get("title"),
            "tags": report_payload.get("tags"),
            "user_id": report_payload.get("user_id"),
            "priority": report_payload.get("priority"),
            "channel": report_payload.get("channel"),
        },
        context,
    )
    if "error" in result:
        return result

    result["city"] = city
    result["converted_unit"] = converted_data.get("to_unit")
    result["workflow"] = "weather_text_brief"
    return result
