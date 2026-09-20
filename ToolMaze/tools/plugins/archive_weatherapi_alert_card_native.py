"""
archive_weatherapi_alert_card_native Tool Plugin

Function: Archive a WeatherAPI-native alert card
Category: Action
Domain: Travel
"""

TOOL_NAME = "archive_weatherapi_alert_card_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    alert_card = arguments.get("alert_card") or {}
    if not isinstance(alert_card, dict):
        return {"error": "alert_card must be an object"}

    result = cdaafd.execute(
        {
            "data": alert_card,
            "title": arguments.get("title") or "Weather Alert",
            "tags": ["weather", "weatherapi", "native"],
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "archived",
        "strategy": "weatherapi_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "weather_ref": alert_card.get("alert_card_id") or "weatherapi_alert_card",
    }
