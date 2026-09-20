"""
publish_visualcrossing_travel_advisory_native Tool Plugin

Function: Publish a Visual Crossing-native travel advisory
Category: Action
Domain: Travel
"""

TOOL_NAME = "publish_visualcrossing_travel_advisory_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    forecast_chip = arguments.get("forecast_chip") or {}
    if not isinstance(forecast_chip, dict):
        return {"error": "forecast_chip must be an object"}

    city = forecast_chip.get("locality") or "Unknown"
    sky = forecast_chip.get("conditions_brief") or "Clear"
    temp = forecast_chip.get("metric_temp", 20)
    level = forecast_chip.get("advice_level") or "normal"
    message = f"Travel advisory for {city}: {sky}, {temp}C ({level})"
    user_id = arguments.get("user_id") or "default_user"

    result = pa.execute(
        {
            "message": message,
            "user_id": user_id,
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "published",
        "strategy": "visualcrossing_advisory_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "weather_ref": forecast_chip.get("forecast_chip_ref") or "visualcrossing_chip",
        "content": result.get("content", message),
    }
