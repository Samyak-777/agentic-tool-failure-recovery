"""
archive_visualcrossing_forecast_chip_native Tool Plugin

Function: Archive a Visual Crossing-native forecast chip
Category: Action
Domain: Travel
"""

TOOL_NAME = "archive_visualcrossing_forecast_chip_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    forecast_chip = arguments.get("forecast_chip") or {}
    if not isinstance(forecast_chip, dict):
        return {"error": "forecast_chip must be an object"}

    result = cdaafd.execute(
        {
            "data": forecast_chip,
            "title": arguments.get("title") or "Forecast Chip",
            "tags": ["weather", "visualcrossing", "native"],
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
        "strategy": "visualcrossing_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "weather_ref": forecast_chip.get("forecast_chip_ref") or "visualcrossing_forecast_chip",
    }
