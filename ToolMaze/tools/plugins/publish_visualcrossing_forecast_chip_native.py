"""
publish_visualcrossing_forecast_chip_native Tool Plugin

Function: Publish a weather notice using a Visual Crossing-native forecast chip
Category: Action
Domain: Travel
"""

TOOL_NAME = "publish_visualcrossing_forecast_chip_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    forecast_chip = arguments.get("forecast_chip") or {}
    if not isinstance(forecast_chip, dict):
        return {"error": "forecast_chip must be an object"}

    city = forecast_chip.get("locality") or "Unknown"
    sky = forecast_chip.get("conditions_brief") or "Clear"
    temp = forecast_chip.get("metric_temp", 20)
    message = f"{city}: {sky}, {temp}C"
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
        "strategy": "visualcrossing_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "weather_ref": forecast_chip.get("forecast_chip_ref") or "vc_chip",
        "content": result.get("content", message),
    }
