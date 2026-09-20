"""
publish_weatherapi_travel_advisory_native Tool Plugin

Function: Publish a WeatherAPI-native travel advisory
Category: Action
Domain: Travel
"""

TOOL_NAME = "publish_weatherapi_travel_advisory_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    alert_card = arguments.get("alert_card") or {}
    if not isinstance(alert_card, dict):
        return {"error": "alert_card must be an object"}

    city = alert_card.get("city_label") or "Unknown"
    sky = alert_card.get("sky_text") or "Clear"
    temp = alert_card.get("celsius_now", 20)
    level = alert_card.get("advice_level") or "normal"
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
        "strategy": "weatherapi_advisory_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "weather_ref": alert_card.get("alert_card_id") or "weatherapi_alert_card",
        "content": result.get("content", message),
    }
