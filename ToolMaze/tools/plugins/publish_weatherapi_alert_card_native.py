"""
publish_weatherapi_alert_card_native Tool Plugin

Function: Publish a weather notice using a WeatherAPI-native alert card
Category: Action
Domain: Travel
"""

TOOL_NAME = "publish_weatherapi_alert_card_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    alert_card = arguments.get("alert_card") or {}
    if not isinstance(alert_card, dict):
        return {"error": "alert_card must be an object"}

    city = alert_card.get("city_label") or "Unknown"
    sky = alert_card.get("sky_text") or "Clear"
    temp = alert_card.get("celsius_now", 20)
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
        "strategy": "weatherapi_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "weather_ref": alert_card.get("alert_card_id") or "wapi_card",
        "content": result.get("content", message),
    }
